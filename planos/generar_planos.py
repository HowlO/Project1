"""Planos de filmación – Salón Meliá Lima (XI Congreso BPW América Latina).

Medidas ESTIMADAS a partir de la fotografía del salón (escala: silla de banquete
estándar ≈ 0.45 m de ancho, paso entre filas ≈ 0.90 m, pantalla ≈ 2.4 m).
Tolerancia ±15 %. Verificar en la visita técnica y ajustar las constantes de
abajo; el script recalcula distancias, ángulos y focales automáticamente.

Uso: python3 generar_planos.py  ->  Planos_Filmacion_Melia.pdf
"""
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle, Wedge

# ---------------------------------------------------------------- medidas (m)
# Origen (0,0): esquina pared de escenario / pared izquierda (vista desde el público).
# x crece hacia la derecha, y crece hacia el fondo del salón.
ANCHO, LARGO = 18.0, 15.0
ALTO_TECHO, ALTO_COFRE = 3.0, 3.3
TARIMA = (5.6, 0.4, 5.2, 2.0, 0.30)          # x, y, ancho, prof, alto
PANTALLA_1 = (2.6, 3.0 * 0 + 0.25, 3.0)      # x, y, ancho
PANTALLA_2 = (11.2, 0.25, 2.6)
PODIO = (6.1, 1.6, 0.6, 0.5)                 # x, y, ancho, prof
MESA = (7.0, 0.8, 3.0, 0.8)
COLUMNA = (13.6, 4.2, 1.2, 1.2)
FILA_0, PASO_FILA, N_FILAS = 3.6, 0.90, 11
SILLA, PASO_SILLA = 0.45, 0.52
BLOQUES = [  # x inicial, sillas por fila, fila inicial
    (1.4, 7, 0),    # bloque izquierdo
    (6.6, 10, 0),   # bloque central
    (13.2, 8, 2),   # bloque derecho (empieza detrás de la columna)
]
PASILLO_CENTRAL = (5.1, 6.5)

# Altura de referencia
H_SENTADO, H_PARADO, H_ORADOR = 1.20, 1.72, TARIMA[4] + 1.62

# Cámaras: x, y, altura de lente, objetivo (x, y), ancho de encuadre (m), color
CAMS = {
    "A": dict(pos=(5.8, 14.3), h=2.20, obj=(8.0, 1.0), ancho=11.0,
              color="#1f6fd1", nombre="Cam A · Plano general fijo",
              equipo="Nikon (Blanca) + trípode alto sobre tarima 0.40 m",
              sensor="Nikon APS-C (factor 1.5)", crop=1.5),
    "B": dict(pos=(0.6, 5.2), h=1.60, obj=(6.4, 1.8), ancho=1.6,
              color="#d1491f", nombre="Cam B · Plano medio + audio",
              equipo="Canon + trípode (Gino) + solapa", sensor="Canon APS-C (factor 1.6)",
              crop=1.6),
}
LUZ = dict(pos=(11.6, 3.3), h=2.4, obj=(6.4, 1.8))


def hfov_deg(dist, ancho):
    return math.degrees(2 * math.atan(ancho / 2 / dist))


def focal_ff(hfov):
    return 36 / (2 * math.tan(math.radians(hfov) / 2))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------------------------------------------------------- dibujo base
def cajetin(fig, titulo, lamina, total):
    ax = fig.add_axes([0.0, 0.0, 1, 0.075])
    ax.axis("off")
    ax.add_patch(Rectangle((0.01, 0.1), 0.98, 0.8, fill=False, lw=1.2, transform=ax.transAxes))
    for x in (0.42, 0.62, 0.80, 0.90):
        ax.plot([x, x], [0.1, 0.9], "k-", lw=0.8, transform=ax.transAxes)
    ax.text(0.02, 0.5, f"XI CONGRESO BPW AMÉRICA LATINA · HOTEL MELIÁ LIMA\n{titulo}",
            va="center", fontsize=10, weight="bold", transform=ax.transAxes)
    ax.text(0.43, 0.5, "Equipo: Gino (B + vigila A) · Antonio (C) · Daniel (C2)\nFecha de rodaje: 16–17 oct 2026",
            va="center", fontsize=8, transform=ax.transAxes)
    ax.text(0.63, 0.5, "Medidas ESTIMADAS desde foto (±15 %)\nVerificar con wincha/láser",
            va="center", fontsize=8, color="#b00000", transform=ax.transAxes)
    ax.text(0.81, 0.5, "Unidades: metros\nRev. 01 · 12/10/2026", va="center", fontsize=8,
            transform=ax.transAxes)
    ax.text(0.945, 0.5, f"LÁMINA\n{lamina}/{total}", va="center", ha="center", fontsize=10,
            weight="bold", transform=ax.transAxes)


def cota(ax, p1, p2, texto, off=0.0, horizontal=True, color="k", fs=7):
    (x1, y1), (x2, y2) = p1, p2
    if horizontal:
        y1 = y2 = y1 + off
    else:
        x1 = x2 = x1 + off
    ax.annotate("", (x1, y1), (x2, y2),
                arrowprops=dict(arrowstyle="<->", lw=0.7, color=color, shrinkA=0, shrinkB=0))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    rot = 0 if horizontal else 90
    ax.text(mx, my, texto, ha="center", va="center", fontsize=fs, rotation=rot, color=color,
            bbox=dict(fc="white", ec="none", pad=0.6))


def salon(ax, sillas_alpha=1.0):
    ax.set_xlim(-1.6, ANCHO + 1.6)
    ax.set_ylim(LARGO + 1.6, -1.8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), ANCHO, LARGO, fill=False, lw=3, ec="#222"))
    # puertas (supuestas al fondo)
    for x in (2.0, 14.5):
        ax.add_patch(Rectangle((x, LARGO - 0.08), 1.6, 0.16, fc="white", ec="#222", lw=1))
        ax.add_patch(Wedge((x, LARGO), 1.6, 270, 360, fc="none", ec="#999", lw=0.6, ls="--"))
        ax.text(x + 0.8, LARGO + 0.45, "Acceso (verificar)", ha="center", fontsize=6, color="#555")
    # tarima, pantallas, podio, mesa
    tx, ty, tw, td, th = TARIMA
    ax.add_patch(Rectangle((tx, ty), tw, td, fc="#e9dfcf", ec="#7a5c3a", lw=1, hatch="..."))
    ax.text(tx + tw / 2, ty + td + 0.25, f"TARIMA h≈{th:.2f}", ha="center", fontsize=6, color="#7a5c3a")
    for (x, y, w), n in ((PANTALLA_1, 1), (PANTALLA_2, 2)):
        ax.add_patch(Rectangle((x, y - 0.06), w, 0.12, fc="#444"))
        ax.text(x + w / 2, y - 0.35, f"PANTALLA {n} ({w:.1f} m)", ha="center", fontsize=6)
    px, py, pw, pd = PODIO
    ax.add_patch(Rectangle((px, py), pw, pd, fc="#8b3a1a", ec="k", lw=0.8))
    ax.text(px + pw / 2, py + pd + 0.25, "PODIO", ha="center", fontsize=6, weight="bold")
    mx, my, mw, md = MESA
    ax.add_patch(Rectangle((mx, my), mw, md, fc="#111"))
    ax.text(mx + mw / 2, my + md / 2, "MESA PRINCIPAL", ha="center", va="center", fontsize=6,
            color="white")
    cx, cy, cw, cd = COLUMNA
    ax.add_patch(Rectangle((cx, cy), cw, cd, fc="#555", ec="k", hatch="///"))
    ax.text(cx + cw / 2, cy - 0.25, "COLUMNA", ha="center", fontsize=6, weight="bold")
    # arreglos florales
    for x in (1.2, 12.9 + 1.0):
        ax.add_patch(Circle((x, 0.8), 0.18, fc="#f2b84b", ec="#a0701a"))
    # sillas
    for x0, n, f0 in BLOQUES:
        for f in range(f0, N_FILAS):
            for s in range(n):
                ax.add_patch(Rectangle((x0 + s * PASO_SILLA, FILA_0 + f * PASO_FILA), SILLA, 0.45,
                                       fc="#2b3f73", ec="#9aa", lw=0.3, alpha=sillas_alpha))


def total_sillas():
    return sum(n * (N_FILAS - f0) for _, n, f0 in BLOQUES)


def cono(ax, cam, alpha=0.13):
    c = CAMS[cam]
    (x, y), (ox, oy) = c["pos"], c["obj"]
    d = dist(c["pos"], c["obj"])
    fov = hfov_deg(d, c["ancho"])
    ang = math.degrees(math.atan2(oy - y, ox - x))
    largo = d * 1.04
    ax.add_patch(Wedge((x, y), largo, ang - fov / 2, ang + fov / 2, fc=c["color"], alpha=alpha,
                       ec=c["color"], lw=0.8))
    ax.plot([x, ox], [y, oy], color=c["color"], lw=0.7, ls="--")
    camara(ax, cam)
    return d, fov


def camara(ax, cam):
    c = CAMS[cam]
    x, y = c["pos"]
    ax.add_patch(Rectangle((x - 0.3, y - 0.2), 0.6, 0.4, fc=c["color"], ec="k", lw=0.8, zorder=5))
    ax.text(x, y, cam, ha="center", va="center", color="white", fontsize=8, weight="bold", zorder=6)


def zona_ciega(ax, origen, color="#c00000"):
    """Sombra de la columna vista desde `origen` (zona sin línea de visión)."""
    cx, cy, cw, cd = COLUMNA
    esquinas = [(cx, cy), (cx + cw, cy), (cx + cw, cy + cd), (cx, cy + cd)]
    angs = sorted(esquinas, key=lambda p: math.atan2(p[1] - origen[1], p[0] - origen[0]))
    a, b = angs[0], angs[-1]

    def extender(p):
        dx, dy = p[0] - origen[0], p[1] - origen[1]
        t = max((LARGO - origen[1]) / dy if dy > 0 else 1e9, 1)
        t = min(t, (ANCHO - origen[0]) / dx if dx > 0 else 1e9)
        return origen[0] + dx * t, origen[1] + dy * t

    pa, pb = extender(a), extender(b)
    pts = [a, pa]
    if abs(pa[1] - LARGO) < 1e-6 and abs(pb[0] - ANCHO) < 1e-6:
        pts.append((ANCHO, LARGO))
    elif abs(pb[1] - LARGO) < 1e-6 and abs(pa[0] - ANCHO) < 1e-6:
        pts.append((ANCHO, LARGO))
    pts += [pb, b]
    ax.add_patch(Polygon(pts, closed=True, fc=color, alpha=0.12, ec=color, ls=":", lw=1))
    return pts


# ---------------------------------------------------------------- láminas
def lamina_planta(pdf, total):
    fig = plt.figure(figsize=(16.54, 11.69))  # A3 horizontal
    ax = fig.add_axes([0.02, 0.09, 0.66, 0.86])
    salon(ax)
    ax.set_title("PLANTA GENERAL · UBICACIÓN DE CÁMARAS, LUZ Y CAMPOS DE VISIÓN  (esc. gráfica)",
                 fontsize=12, weight="bold", loc="left")
    zona_ciega(ax, (PODIO[0] + PODIO[2] / 2, PODIO[1]))
    ax.text(15.6, 13.9, "ZONA CIEGA: la columna tapa el podio · NO poner cámaras fijas",
            fontsize=7, color="#c00000", ha="center", weight="bold",
            bbox=dict(fc="white", ec="#c00000", pad=2, lw=0.6))
    datos = {k: cono(ax, k) for k in CAMS}
    # luz
    lx, ly = LUZ["pos"]
    ax.add_patch(Circle((lx, ly), 0.28, fc="#ffd400", ec="k", zorder=5))
    ax.text(lx, ly, "L", ha="center", va="center", fontsize=8, weight="bold", zorder=6)
    ang = math.degrees(math.atan2(LUZ["obj"][1] - ly, LUZ["obj"][0] - lx))
    ax.add_patch(Wedge((lx, ly), dist(LUZ["pos"], LUZ["obj"]), ang - 15, ang + 15, fc="#ffd400",
                       alpha=0.22, ec="#c9a400"))
    # Cam C zona de trabajo
    ax.add_patch(Rectangle(PASILLO_CENTRAL[:1] + (FILA_0 - 1.0,), PASILLO_CENTRAL[1] - PASILLO_CENTRAL[0],
                           LARGO - FILA_0 - 0.4, fc="#2e9b4f", alpha=0.10, ec="#2e9b4f", ls="--"))
    ax.add_patch(Rectangle((ANCHO - 0.75, 5.5), 0.6, 8.8, fc="#2e9b4f", alpha=0.10, ec="#2e9b4f", ls="--"))
    ax.text(5.8, 8.5, "PASILLO\nCam C /\ndesfile", ha="center", fontsize=6.5, color="#1d6b35",
            weight="bold", rotation=90)
    ax.text(ANCHO - 0.45, 10, "Lateral der. Cam C (público)", rotation=90, fontsize=6,
            color="#1d6b35", ha="center", va="center")
    # cables y tomas
    for (x, y), lab in (((0.0, 5.2), "T1"), ((5.8, LARGO), "T2"), ((ANCHO, 3.3), "T3")):
        ax.add_patch(Rectangle((x - 0.15, y - 0.15), 0.3, 0.3, fc="white", ec="k", zorder=5))
        ax.text(x, y, "⏚" if False else lab[1], ha="center", va="center", fontsize=6, zorder=6)
    ax.plot([5.8, 5.8], [14.5, LARGO], color="#888", lw=1.2, ls="-.")
    ax.plot([0.3, 0.0], [5.2, 5.2], color="#888", lw=1.2, ls="-.")
    ax.plot([11.9, ANCHO], [3.3, 3.3], color="#888", lw=1.2, ls="-.")
    # cotas generales
    cota(ax, (0, -1.2), (ANCHO, -1.2), f"{ANCHO:.1f} m (est.)", fs=8)
    cota(ax, (-1.1, 0), (-1.1, LARGO), f"{LARGO:.1f} m (est.)", horizontal=False, fs=8)
    cota(ax, (0, FILA_0), (0, 0), f"{FILA_0:.1f}", horizontal=False, off=-0.45)
    cota(ax, (PASILLO_CENTRAL[0], 2.95), (PASILLO_CENTRAL[1], 2.95), f"{PASILLO_CENTRAL[1]-PASILLO_CENTRAL[0]:.1f}")
    # distancias cámara-objetivo
    for k, (d, fov) in datos.items():
        c = CAMS[k]
        mx = (c["pos"][0] + c["obj"][0]) / 2
        my = (c["pos"][1] + c["obj"][1]) / 2
        ax.text(mx + 0.3, my, f"{d:.1f} m", fontsize=8, color=c["color"], weight="bold",
                bbox=dict(fc="white", ec=c["color"], pad=1.5, lw=0.6))
    # escala gráfica y norte de escenario
    for i in range(5):
        ax.add_patch(Rectangle((ANCHO - 5 + i, LARGO + 1.0), 1, 0.2, fc="k" if i % 2 == 0 else "white", ec="k", lw=0.6))
    ax.text(ANCHO - 2.5, LARGO + 1.5, "0     1     2     3     4     5 m", ha="center", fontsize=7)
    ax.annotate("▼ ESCENARIO", (8.2, -0.5), fontsize=8, weight="bold", ha="center")

    # leyenda / notas
    ax2 = fig.add_axes([0.70, 0.09, 0.29, 0.86])
    ax2.axis("off")
    y = 0.98
    ax2.text(0, y, "LEYENDA", fontsize=11, weight="bold")
    y -= 0.04
    items = [("#1f6fd1", "A", "Cam A – plano general fijo (Gino vigila)"),
             ("#d1491f", "B", "Cam B – plano medio + audio · Gino"),
             ("#2e9b4f", "C", "Cam C – estabilizador · Antonio"),
             ("#7b3fb5", "D", "Apoyo C2 – iPhone + gimbal · Daniel"),
             ("#ffd400", "L", "Luz de relleno 45° (Cheng) · Gino"),
             ("white", "T", "Tomacorriente supuesto (verificar)"),
             ("#c00000", "", "Zona ciega por la columna"),
             ("#888", "", "Recorrido de cable (pegar con cinta)")]
    for col, lab, txt in items:
        ax2.add_patch(Rectangle((0, y - 0.012), 0.05, 0.024, fc=col, ec="k", lw=0.6,
                                alpha=0.5 if lab == "" else 1))
        ax2.text(0.025, y, lab, ha="center", va="center", fontsize=8, weight="bold",
                 color="white" if col not in ("#ffd400", "white") else "k")
        ax2.text(0.08, y, txt, va="center", fontsize=9)
        y -= 0.035
    y -= 0.02
    ax2.text(0, y, "DATOS ESTIMADOS DEL SALÓN", fontsize=11, weight="bold"); y -= 0.035
    for t in [f"Planta ≈ {ANCHO:.0f} × {LARGO:.0f} m  ≈ {ANCHO*LARGO:.0f} m²",
              f"Altura techo ≈ {ALTO_TECHO:.1f} m (cofre ≈ {ALTO_COFRE:.1f} m)",
              f"Aforo teatro dibujado ≈ {total_sillas()} sillas",
              f"{N_FILAS} filas · paso {PASO_FILA:.2f} m · silla {SILLA:.2f} m",
              "Escala tomada de: silla de banquete,",
              "pantalla de proyección y paso de filas."]:
        ax2.text(0, y, "• " + t, fontsize=9); y -= 0.03
    y -= 0.02
    ax2.text(0, y, "NOTAS DE RODAJE", fontsize=11, weight="bold"); y -= 0.035
    notas = [
        "1. Cam A fija en el eje del pasillo: único punto",
        "   sin obstrucción que ve podio + mesa.",
        "2. Cam A sobre tarima/cajón 0.40 m: en el Himno",
        "   el público se para y tapa un trípode normal.",
        "3. Cam B pegada a la pared izquierda (fila 2–3):",
        "   orador del podio en ¾ de cara.",
        "4. Luz al lado opuesto de Cam B, fuera del haz",
        "   de los proyectores; no apuntar a pantallas.",
        "5. Cam C nunca cruza el eje A→escenario durante",
        "   discursos; se mueve por laterales.",
        "6. Cables por paredes, pegados con cinta;",
        "   nunca por el pasillo del desfile.",
        "7. Medir en la visita técnica (jueves 15) y",
        "   corregir este plano (script parametrizado).",
    ]
    for t in notas:
        ax2.text(0, y, t, fontsize=8.5, family="monospace"); y -= 0.026
    cajetin(fig, "LÁMINA 01 · PLANTA GENERAL DE CÁMARAS", 1, total)
    pdf.savefig(fig); plt.close(fig)


def lamina_corte(pdf, total):
    fig = plt.figure(figsize=(16.54, 11.69))
    ax = fig.add_axes([0.05, 0.50, 0.90, 0.42])
    ax.set_title("CORTE LONGITUDINAL (eje del pasillo) · LÍNEA DE VISIÓN Cam A → ORADOR",
                 fontsize=12, weight="bold", loc="left")
    ax.set_xlim(-0.8, LARGO + 0.8); ax.set_ylim(-0.3, ALTO_COFRE + 0.6)
    ax.set_aspect("equal")
    ax.axhline(0, color="k", lw=2)
    ax.plot([0, LARGO], [ALTO_TECHO, ALTO_TECHO], "k-", lw=1.5)
    ax.plot([2.5, 9.5], [ALTO_COFRE, ALTO_COFRE], "k-", lw=1); ax.text(6, ALTO_COFRE + 0.08, "cofre iluminado", fontsize=7, ha="center")
    ax.plot([0, 0], [0, ALTO_TECHO], "k-", lw=2); ax.plot([LARGO, LARGO], [0, ALTO_TECHO], "k-", lw=2)
    th = TARIMA[4]
    ax.add_patch(Rectangle((TARIMA[1], 0), TARIMA[3], th, fc="#e9dfcf", ec="#7a5c3a", hatch=".."))
    # orador
    oy = PODIO[1]
    ax.add_patch(Rectangle((oy - 0.2, th), 0.4, 1.15, fc="#8b3a1a"))
    ax.add_patch(Rectangle((oy + 0.25, th), 0.25, 1.45, fc="#777"))
    ax.add_patch(Circle((oy + 0.37, H_ORADOR), 0.11, fc="#777"))
    ax.text(oy + 0.37, H_ORADOR + 0.25, "orador", fontsize=7, ha="center")
    # pantalla
    ax.add_patch(Rectangle((0.2, 0.95), 0.08, 1.8, fc="#444")); ax.text(0.45, 2.85, "pantalla", fontsize=7)
    # filas de público
    for f in range(N_FILAS):
        y = FILA_0 + f * PASO_FILA + 0.2
        ax.add_patch(Circle((y, H_SENTADO - 0.1), 0.1, fc="#2b3f73", alpha=0.8))
        ax.add_patch(Circle((y, H_PARADO - 0.1), 0.1, fc="none", ec="#c00000", ls=":"))
    ax.text(FILA_0 + 4, H_SENTADO - 0.45, f"público sentado (cabeza ≈ {H_SENTADO:.2f} m)", fontsize=8, color="#2b3f73")
    ax.text(FILA_0 + 4, H_PARADO - 0.42, f"público de pie – Himno (cabeza ≈ {H_PARADO:.2f} m)", fontsize=8, color="#c00000")
    # cam A + tarima
    a = CAMS["A"]; ay = a["pos"][1]
    ax.add_patch(Rectangle((ay - 0.4, 0), 0.8, 0.40, fc="#bbb", ec="k"))
    ax.plot([ay, ay], [0.4, a["h"]], "k-", lw=2)
    ax.add_patch(Rectangle((ay - 0.15, a["h"] - 0.1), 0.3, 0.2, fc=a["color"], ec="k"))
    ax.text(ay + 0.3, a["h"], f"Cam A  h lente = {a['h']:.2f} m\n(trípode 1.80 + cajón 0.40)", fontsize=8, color=a["color"], va="center")
    ax.plot([ay, oy + 0.37], [a["h"], H_ORADOR], color=a["color"], lw=1.5)
    # línea con trípode sin cajón
    ax.plot([ay, oy + 0.37], [1.80, H_ORADOR], color="#c00000", lw=1, ls="--")
    ax.text(ay - 3.2, 1.98, "sin cajón (1.80 m): roza cabezas de pie ✗", fontsize=7.5, color="#c00000")
    # cam B
    ax.text(5.6, 2.75, f"Cam B h = {CAMS['B']['h']:.2f} m (lateral, fuera del corte)", fontsize=7.5, color=CAMS["B"]["color"])
    cota(ax, (0, -0.2), (LARGO, -0.2), f"{LARGO:.1f} m")
    cota(ax, (LARGO + 0.4, 0), (LARGO + 0.4, ALTO_TECHO), f"{ALTO_TECHO:.1f}", horizontal=False)
    cota(ax, (ay, 0.05), (oy + 0.37, 0.05), f"Cam A → orador ≈ {dist(a['pos'], (PODIO[0]+0.3, PODIO[1])):.1f} m (planta)", off=0.0)
    ax.axis("off")

    # márgenes de altura
    ax3 = fig.add_axes([0.05, 0.10, 0.90, 0.33]); ax3.axis("off")
    ax3.text(0, 0.95, "VERIFICACIÓN DE LÍNEA DE VISIÓN (última fila de pie, a 0.9 m delante de Cam A)", fontsize=11, weight="bold")
    fila_ult = FILA_0 + (N_FILAS - 1) * PASO_FILA + 0.2
    filas = []
    for h in (1.60, 1.80, 2.20):
        t = (a["pos"][1] - fila_ult) / (a["pos"][1] - (oy + 0.37))
        hl = h + (H_ORADOR - h) * t
        margen = hl - H_PARADO
        filas.append((f"{h:.2f} m", f"{hl:.2f} m", f"{margen*100:+.0f} cm", "OK" if margen > 0.15 else "RIESGO"))
    tbl = ax3.table(cellText=filas, colLabels=["Altura lente Cam A", "Línea de visión sobre última fila",
                                                "Margen vs. cabeza de pie (1.72)", "Resultado"],
                    loc="upper left", bbox=[0, 0.45, 0.7, 0.42], cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(10)
    ax3.text(0, 0.30, "Conclusión: con 1.60–1.80 m la cámara queda tapada en el Himno y los aplausos de pie.\n"
                      "Usar cajón/tarima de 0.40 m o pedir al hotel una tarima de prensa al fondo (lente ≈ 2.20 m).\n"
                      "El techo (≈ 3.0 m) deja margen suficiente; no hay riesgo de que aparezca en cuadro.",
             fontsize=10, va="top")
    cajetin(fig, "LÁMINA 02 · CORTE Y LÍNEAS DE VISIÓN", 2, total)
    pdf.savefig(fig); plt.close(fig)


def lamina_ficha(pdf, total):
    fig = plt.figure(figsize=(16.54, 11.69))
    ax = fig.add_axes([0.03, 0.10, 0.94, 0.85]); ax.axis("off")
    ax.text(0, 0.98, "FICHA TÉCNICA DE CÁMARAS · DISTANCIAS, ÁNGULOS Y FOCALES RECOMENDADAS",
            fontsize=13, weight="bold")
    filas = []
    tomas = [
        ("A", "Escenario completo (pantallas + podio + mesa)", CAMS["A"]["pos"], (8.0, 1.0), 11.0),
        ("A", "Plano general cerrado (podio + mesa)", CAMS["A"]["pos"], (8.0, 1.2), 5.0),
        ("B", "Orador en podio · plano medio (cintura)", CAMS["B"]["pos"], (6.4, 1.8), 1.6),
        ("B", "Orador en podio · primer plano", CAMS["B"]["pos"], (6.4, 1.8), 0.8),
        ("B", "Mesa principal completa", CAMS["B"]["pos"], (8.5, 1.2), 3.4),
        ("B", "Autoridad en mesa · plano medio", CAMS["B"]["pos"], (8.5, 1.2), 1.4),
    ]
    for cam, desc, p, o, w in tomas:
        d = dist(p, o); f = hfov_deg(d, w); ff = focal_ff(f); crop = CAMS[cam]["crop"]
        filas.append([cam, desc, f"{d:.1f}", f"{w:.1f}", f"{f:.1f}°", f"{ff:.0f} mm", f"{ff/crop:.0f} mm"])
    t = ax.table(cellText=filas,
                 colLabels=["Cam", "Encuadre", "Distancia (m)", "Ancho de cuadro (m)", "Ángulo horiz.",
                            "Focal full-frame", "Focal real en APS-C"],
                 bbox=[0, 0.56, 1, 0.38], cellLoc="center", colWidths=[0.05, 0.33, 0.1, 0.12, 0.1, 0.13, 0.17])
    t.auto_set_font_size(False); t.set_fontsize(10)
    for (r, c), cell in t.get_celld().items():
        if r == 0:
            cell.set_facecolor("#222"); cell.set_text_props(color="white", weight="bold")
        elif c == 0:
            cell.set_facecolor(CAMS[filas[r - 1][0]]["color"]); cell.set_text_props(color="white", weight="bold")
    texto = (
        "LECTURA DE LA TABLA\n"
        "• Cam A: un zoom estándar (18–55 mm en APS-C) cubre todo, entre 25 y 55 mm.\n"
        "• Cam B: necesita TELE. Para plano medio/primer plano del podio desde 7 m hacen falta ≈ 100–200 mm reales.\n"
        "   Si la Canon solo tiene 18–55 mm: acercar Cam B a 3–4 m del podio (fila 1, pared izq.) o alquilar un 55–250 mm.\n"
        "• Cam C (estabilizador): gran angular 18–24 mm reales; acercarse al sujeto en vez de usar zoom.\n"
        "• Apoyo C2 (Daniel, iPhone + gimbal): lente 1x (26 mm eq.); evitar el zoom digital. 2x solo con buena luz.\n\n"
        "AJUSTES COMUNES (todas las cámaras iguales, incl. iPhone, para que empaten en edición)\n"
        "• 1080p o 4K · 25 fps (o 24/30, pero el mismo en todas) · obturación 1/50 (1/60 si es 30 fps) — evita parpadeo de luces/proyector.\n"
        "• Balance de blancos MANUAL ≈ 3400 K (medir con tarjeta gris en la tarima) · ISO máx. 1600–3200.\n"
        "• Exponer para la piel del orador; aceptar pantalla quemada. Zebra 70 % en caras si la cámara lo permite.\n"
        "• Fecha/hora sincronizada · aplauso o claqueta al inicio de cada bloque para sincronizar audio.\n\n"
        "LUZ\n"
        f"• Posición L a {dist(LUZ['pos'], LUZ['obj']):.1f} m del podio, altura {LUZ['h']:.1f} m, ≈45° del eje del orador, lado opuesto a Cam B.\n"
        "• Temperatura 3200–3500 K, intensidad baja (relleno). No apuntar a pantallas ni a los ojos del orador.\n\n"
        "PENDIENTE DE MEDIR EN VISITA TÉCNICA: ancho y largo reales, posición exacta de la columna, altura de tarima,\n"
        "ubicación de tomacorrientes y accesos. Con esas medidas se corrige el script y se regeneran las láminas."
    )
    ax.text(0, 0.50, texto, fontsize=10.5, va="top", linespacing=1.5)
    cajetin(fig, "LÁMINA 03 · FICHA TÉCNICA", 3, total)
    pdf.savefig(fig); plt.close(fig)


MORADO = "#7b3fb5"  # Daniel · apoyo C2 (iPhone)

EQUIPO = [
    ("Gino", "Cam B · Canon + trípode + solapa  ·  vigila Cam A  ·  Luz",
     "Oradoras y autoridades en plano medio/cerrado; audio principal. Revisa grabación/batería de Cam A en cada pausa."),
    ("Antonio", "Cam C · Nikon propia + estabilizador",
     "Móvil principal: desfile, público, detalles. Dirección, enlace con la organización y respaldo de tarjetas."),
    ("Daniel", "Apoyo C2 · iPhone + gimbal de celular",
     "Tomas de apoyo: verticales 9:16 para reels, backstage, detalles, 2.º ángulo de desfile, velas y EXPO."),
    ("—", "Cam A · Nikon (Blanca) + trípode alto",
     "FIJA sin operador: toma maestra del escenario de principio a fin (ver láminas 01 y 02)."),
]

# Hora, programa, Cam A (fija), Cam B · Gino, Cam C · Antonio, C2 · Daniel
VIERNES = [
    ("06:30–07:30", "Llegada y montaje", "Montar en cajón 0.40 m", "Audio, luz, monta Cam A", "Balance de blancos", "Prueba gimbal, WB iPhone"),
    ("07:30–08:00", "Llegada de delegaciones", "Encuadre fijado", "Prueba de solapa", "Ingreso, banderas", "Backstage, backdrop (9:16)"),
    ("08:00–09:30", "INAUGURACIÓN (prioridad)", "REC continuo", "Autoridades / podio", "Desfile de frente, Himno", "Desfile desde escenario, detalles"),
    ("09:30–10:30", "Ejecutivo Internacional", "REC", "Oradoras", "Respaldo tarjetas", "Público, detalles (9:16)"),
    ("10:30–11:00", "Pausa café + EXPO", "Pausa / batería (Gino)", "Baterías, revisa Cam A", "Corte de cinta", "Stands, networking (9:16)"),
    ("11:00–13:15", "Ejecutivo Internacional", "REC", "Intervenciones clave", "Selectivo, por turnos", "Reacciones, por turnos"),
    ("13:15–14:45", "Almuerzo", "Pausa / batería", "Descanso", "Brindis 15–20 min", "Ambiente almuerzo, descarga iPhone"),
    ("14:50–16:45", "Mesas redondas", "Pausa (o panel general)", "Panelista que habla", "Público que pregunta", "Mesas no cubiertas por C"),
    ("16:50–17:20", "Pausa café + EXPO", "Pausa", "Luz testimonios", "Testimonios cortos", "Stands, verticales"),
    ("17:25–18:15", "Espacio «Joven»", "REC", "Oradoras", "Público, reacciones", "Verticales del espacio Joven"),
    ("18:15–19:00", "Conclusiones", "REC + desmontaje", "Desmontaje audio/luz", "Respaldo final", "Cierre, salida de asistentes"),
]
SABADO = [
    ("07:15–08:30", "Llegada y montaje", "Montar en cajón", "Audio, luz, Cam A", "Balance de blancos", "Prueba gimbal"),
    ("08:30–09:15", "Conf. Lilian Pinos", "REC", "Oradora", "Público, detalles", "Verticales, reacciones"),
    ("09:20–10:30", "Estatuto (no se filma)", "—", "Descanso", "Preselección Reel 2", "Descarga iPhone"),
    ("10:35–11:05", "Pausa café + EXPO", "Pausa / batería", "Revisa Cam A", "Stands", "Stands, networking (9:16)"),
    ("11:10–12:00", "Conf. Brenda Hidalgo", "REC", "Oradora", "Público, detalles", "Verticales, reacciones"),
    ("12:05–12:40", "Presidentas + Muro", "REC", "Cada presidenta", "Muro de Impacto", "Detalle de cada proyecto"),
    ("12:40–17:45", "Desmontaje / receso", "Guardar", "—", "—", "—"),
    ("17:45–19:00", "Preparación de gala", "Ubicar en salón de gala", "Audio, baja luz", "Llegada invitadas", "Decoración, mesas, velas"),
    ("19:00–23:00", "VELAS + CENA DE GALA", "REC (ISO alto)", "Reconoc., firma (+luz)", "Velas, firma", "Velas en cerrado, ambiente (9:16)"),
    ("23:00–23:30", "Cierre", "Desmontaje", "Desmontaje", "Respaldo final", "Descarga iPhone"),
]


def tabla_horario(ax, filas, bbox):
    t = ax.table(cellText=[list(f) for f in filas],
                 colLabels=["Hora", "Programa", "Cam A · fija", "Cam B · Gino", "Cam C · Antonio",
                            "Apoyo C2 · Daniel (iPhone)"],
                 bbox=bbox, cellLoc="left", colWidths=[0.08, 0.16, 0.15, 0.18, 0.19, 0.24])
    t.auto_set_font_size(False); t.set_fontsize(8)
    colores = [None, None, CAMS["A"]["color"], CAMS["B"]["color"], "#2e9b4f", MORADO]
    for (r, c), cell in t.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor(colores[c] or "#222"); cell.set_text_props(color="white", weight="bold")
        elif filas[r - 1][1].isupper() or "(prioridad)" in filas[r - 1][1]:
            cell.set_facecolor("#fff3d6")


def lamina_equipo(pdf, total):
    fig = plt.figure(figsize=(16.54, 11.69))
    ax = fig.add_axes([0.03, 0.09, 0.94, 0.88]); ax.axis("off")
    ax.text(0, 1.0, "EQUIPO Y ASIGNACIÓN DE TOMAS POR HORARIO", fontsize=13, weight="bold")
    t = ax.table(cellText=[list(e) for e in EQUIPO], colLabels=["Persona", "Puesto / equipo", "Función"],
                 bbox=[0, 0.82, 1, 0.155], cellLoc="left", colWidths=[0.07, 0.30, 0.63])
    t.auto_set_font_size(False); t.set_fontsize(9)
    for (r, c), cell in t.get_celld().items():
        if r == 0:
            cell.set_facecolor("#222"); cell.set_text_props(color="white", weight="bold")
    ax.text(0, 0.795, "VIERNES 16 – Mujeres que abren caminos", fontsize=11, weight="bold")
    tabla_horario(ax, VIERNES, [0, 0.42, 1, 0.365])
    ax.text(0, 0.395, "SÁBADO 17 – Mujeres que transforman", fontsize=11, weight="bold")
    tabla_horario(ax, SABADO, [0, 0.06, 1, 0.325])
    ax.text(0, 0.01, "iPhone: grabar 4K 25 fps con app de control manual (p. ej. Blackmagic Camera), WB 3400 K fijo, "
            "obturación 1/50, bloquear AE/AF. Vertical 9:16 para reels.  Filas resaltadas = prioridad máxima.",
            fontsize=8.5, style="italic")
    cajetin(fig, "LÁMINA 05 · EQUIPO Y ASIGNACIÓN POR HORARIO", 5, total)
    pdf.savefig(fig); plt.close(fig)


def lamina_momentos(pdf, total):
    fig = plt.figure(figsize=(16.54, 11.69))
    momentos = [
        ("INAUGURACIÓN · desfile de banderas e Himno (A+B+C)", "desfile"),
        ("PONENCIAS / EJECUTIVO (A+B, C en pausas)", "ponencia"),
        ("MESAS REDONDAS (B+C)", "mesas"),
        ("RECONOCIMIENTOS / FIRMA DE CONVENIO (A+B+C+Luz)", "firma"),
    ]
    for i, (tit, modo) in enumerate(momentos):
        ax = fig.add_axes([0.01 + (i % 2) * 0.495, 0.535 - (i // 2) * 0.45, 0.48, 0.42])
        salon(ax, sillas_alpha=0.35)
        ax.set_title(tit, fontsize=10, weight="bold", loc="left")
        if modo in ("desfile", "ponencia", "firma"):
            cono(ax, "A", 0.08)
        if modo in ("desfile", "ponencia", "firma", "mesas"):
            cono(ax, "B", 0.10)
        verde = "#2e9b4f"
        if modo == "desfile":
            ax.add_patch(FancyArrowPatch((5.8, LARGO - 0.3), (5.8, 3.0), arrowstyle="-|>", mutation_scale=18, color="#d4a017", lw=3))
            ax.text(5.15, 9.5, "BANDERAS", rotation=90, fontsize=7, color="#a07000", weight="bold")
            ax.add_patch(FancyArrowPatch((5.9, 4.5), (5.9, 11.0), arrowstyle="-|>", mutation_scale=14, color=verde, lw=1.5, ls="--"))
            ax.text(6.3, 6.2, "C1: de frente,\nretrocediendo", fontsize=6.5, color=verde)
            ax.add_patch(Circle((5.8, 13.6), 0.25, fc=verde)); ax.text(6.2, 13.4, "C2: contraplano\ndesde atrás", fontsize=6.5, color=verde)
            ax.add_patch(Circle((4.7, 2.9), 0.25, fc=verde)); ax.text(2.0, 2.6, "C3: Himno\nplano bajo", fontsize=6.5, color=verde)
            ax.add_patch(Circle((11.0, 2.9), 0.25, fc=MORADO)); ax.text(11.4, 3.2, "D: banderas llegando\n(desde escenario, 9:16)", fontsize=6.5, color=MORADO)
        elif modo == "ponencia":
            ax.add_patch(Circle((ANCHO - 0.5, 7.5), 0.25, fc=verde)); ax.text(14.5, 8.4, "C: reacciones\ndel público", fontsize=6.5, color=verde)
            ax.add_patch(Circle((0.5, 11.0), 0.25, fc=MORADO)); ax.text(1.0, 12.3, "D: público y detalles\n(lateral izq., 9:16)", fontsize=6.5, color=MORADO)
            ax.add_patch(Circle((5.8, 3.1), 0.25, fc=verde)); ax.text(3.0, 2.9, "C: detalles\n(sólo en pausas)", fontsize=6.5, color=verde)
        elif modo == "mesas":
            ax.add_patch(Circle((11.0, 3.0), 0.25, fc=verde)); ax.text(11.4, 2.8, "C: lateral der.\n(panelistas en ¾)", fontsize=6.5, color=verde)
            ax.add_patch(Circle((3.5, 9.0), 0.25, fc=verde)); ax.text(2.3, 9.8, "C: público\nque pregunta", fontsize=6.5, color=verde)
            ax.add_patch(Circle((15.5, 13.0), 0.25, fc=MORADO)); ax.text(13.0, 12.4, "D: otra mesa /\nverticales", fontsize=6.5, color=MORADO)
            ax.text(8.5, 2.6, "Cam B gira a mesa completa", fontsize=6.5, color=CAMS["B"]["color"], ha="center")
        elif modo == "firma":
            lx, ly = LUZ["pos"]
            ax.add_patch(Circle((lx, ly), 0.28, fc="#ffd400", ec="k", zorder=5)); ax.text(lx, ly, "L", ha="center", va="center", fontsize=7, zorder=6)
            ax.add_patch(Circle((10.6, 2.0), 0.25, fc=verde)); ax.text(10.9, 2.6, "C: cerrado a manos\n/ firma (lado mesa)", fontsize=6.5, color=verde)
            ax.add_patch(Circle((5.8, 3.2), 0.25, fc=verde)); ax.text(2.4, 3.2, "C: foto oficial\n(frontal)", fontsize=6.5, color=verde)
            ax.add_patch(Circle((3.0, 6.5), 0.25, fc=MORADO)); ax.text(1.0, 7.6, "D: velas y reacciones\n(cerrado, 9:16)", fontsize=6.5, color=MORADO)
    cajetin(fig, "LÁMINA 04 · POSICIONES POR MOMENTO DEL PROGRAMA", 4, total)
    pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    salida = Path(__file__).with_name("Planos_Filmacion_Melia.pdf")
    total = 5
    with PdfPages(salida) as pdf:
        lamina_planta(pdf, total)
        lamina_corte(pdf, total)
        lamina_momentos(pdf, total)
        lamina_ficha(pdf, total)
        lamina_equipo(pdf, total)
    print("OK ->", salida, "| sillas dibujadas:", total_sillas())
