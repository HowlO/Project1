#!/usr/bin/env python3
"""
Protector de prompts: quita datos personales de un texto ANTES de pegarlo
en una IA (Claude, Grok, Gemini, ChatGPT...). Funciona 100% local, sin
internet y sin librerías externas.

Uso:
  python protector_prompts.py proteger  < prompt.txt      -> texto limpio
  python protector_prompts.py restaurar < respuesta.txt   -> vuelve a poner tus datos
  python protector_prompts.py revisar   < prompt.txt      -> solo avisa qué encontró (código 1 si hay riesgo)
  python protector_prompts.py borrar                      -> elimina el mapa local

Windows (PowerShell), usando el portapapeles:
  Get-Clipboard | python protector_prompts.py proteger | Set-Clipboard
"""
import json
import os
import re
import sys
from pathlib import Path

CARPETA = Path.home() / ".protector_prompts"
MAPA = CARPETA / "mapa.json"            # placeholder -> dato real (nunca sale de tu equipo)
SENSIBLES = CARPETA / "sensibles.txt"   # tus palabras propias: nombre, dirección, familiares...


def luhn_valido(numero):
    digitos = [int(d) for d in numero][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2)
                for i, d in enumerate(digitos))
    return total % 10 == 0


def es_tarjeta(texto):
    numero = re.sub(r"\D", "", texto)
    return 13 <= len(numero) <= 19 and luhn_valido(numero)


# (tipo, patrón, nivel de riesgo, validador opcional). El orden importa:
# primero lo más específico para que un número largo no se lea como DNI.
REGLAS = [
    ("CLAVE", re.compile(r"(?i)\b(?:contraseña|contrasena|password|clave|pin|token)\s*[:=]\s*\S+"), "ALTO", None),
    ("API_KEY", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[A-Za-z0-9]{36,}|xox[abp]-[A-Za-z0-9-]{10,})\b"), "ALTO", None),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "MEDIO", None),
    ("TARJETA", re.compile(r"\b(?:\d[ -]?){12,18}\d\b"), "ALTO", es_tarjeta),
    ("CCI", re.compile(r"\b\d{3}-?\d{3}-?\d{12}-?\d{2}\b"), "ALTO", None),
    ("CUENTA", re.compile(r"\b\d{3}-\d{7,8}-\d-\d{2}\b|\b\d{13,14}\b"), "ALTO", None),
    ("RUC", re.compile(r"\b(?:10|15|17|20)\d{9}\b"), "MEDIO", None),
    ("TELEFONO", re.compile(r"(?:\+?51[ -]?)?\b9\d{2}[ -]?\d{3}[ -]?\d{3}\b"), "MEDIO", None),
    ("DNI", re.compile(r"\b\d{8}\b"), "MEDIO", None),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[0-9a-fA-F]{1,4}:){4,7}[0-9a-fA-F]{1,4}\b"), "MEDIO", None),
]


def cargar_mapa():
    try:
        return json.loads(MAPA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar_mapa(mapa):
    CARPETA.mkdir(mode=0o700, exist_ok=True)
    MAPA.write_text(json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8")
    os.chmod(MAPA, 0o600)


def palabras_sensibles():
    try:
        lineas = SENSIBLES.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    # Las más largas primero para que "Juan Pérez" gane a "Juan"
    return sorted({l.strip() for l in lineas if l.strip() and not l.startswith("#")}, key=len, reverse=True)


def proteger(texto):
    mapa = cargar_mapa()
    inverso = {real: marca for marca, real in mapa.items()}
    hallazgos = []

    def marcar(tipo, real, riesgo):
        if real not in inverso:
            n = sum(1 for m in mapa if m.startswith(f"[{tipo}_")) + 1
            marca = f"[{tipo}_{n}]"
            mapa[marca] = real
            inverso[real] = marca
        hallazgos.append((tipo, riesgo))
        return inverso[real]

    for palabra in palabras_sensibles():
        patron = re.compile(r"\b" + re.escape(palabra) + r"\b", re.IGNORECASE)
        texto = patron.sub(lambda m: marcar("PERSONAL", m.group(0), "ALTO"), texto)

    for tipo, patron, riesgo, validar in REGLAS:
        def reemplazar(m, tipo=tipo, riesgo=riesgo, validar=validar):
            if validar and not validar(m.group(0)):
                return m.group(0)
            return marcar(tipo, m.group(0), riesgo)
        texto = patron.sub(reemplazar, texto)

    guardar_mapa(mapa)
    return texto, hallazgos


def restaurar(texto):
    for marca, real in cargar_mapa().items():
        texto = texto.replace(marca, real)
    return texto


def resumen(hallazgos):
    if not hallazgos:
        return "✅ No se encontraron datos sensibles."
    conteo = {}
    for tipo, riesgo in hallazgos:
        conteo[(tipo, riesgo)] = conteo.get((tipo, riesgo), 0) + 1
    lineas = [f"  - {tipo}: {n} (riesgo {riesgo})" for (tipo, riesgo), n in sorted(conteo.items())]
    return "⚠️  Datos sensibles encontrados y ocultados:\n" + "\n".join(lineas)


def main():
    accion = sys.argv[1] if len(sys.argv) > 1 else "proteger"
    if accion == "borrar":
        MAPA.unlink(missing_ok=True)
        print("Mapa local eliminado.", file=sys.stderr)
        return 0

    texto = sys.stdin.read()
    if accion == "restaurar":
        sys.stdout.write(restaurar(texto))
        return 0

    limpio, hallazgos = proteger(texto)
    print(resumen(hallazgos), file=sys.stderr)  # el aviso va a stderr: no se copia al portapapeles
    if accion == "revisar":
        return 1 if hallazgos else 0
    sys.stdout.write(limpio)
    return 0


if __name__ == "__main__":
    sys.exit(main())
