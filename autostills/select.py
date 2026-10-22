"""Puntuación y elección de stills dentro de un plano (docs/criterios.md).

Dos pasadas (D17): lo barato (métricas.py) en todos los frames → preselección de candidatos diversos →
caras, saliencia y estética (faces.py) solo en los candidatos → elección final de N stills distintos.
Todo se compara dentro del plano (ranking 0..1); una señal que no aplica (None) no resta: su peso se reparte.
"""
import numpy as np

# shortcut: pesos a ojo hasta la prueba de pesos contra stills elegidos por el owner (D6, docs/criterios.md)
PRESETS = {
    "gallery": {"sharp": 3, "still": 2, "exposure": 2, "focus_stable": 1, "tonal": 1, "skin": 1, "representative": 0.5,
                "face_present": 1, "face_sharp": 2, "face_quality": 1.5, "eyes_open": 1.5, "mouth_closed": 0.5, "frontal": 0.5,
                "face_complete": 1, "no_text": 1},
    "social": {"sharp": 3, "still": 2, "exposure": 1.5, "focus_stable": 1, "face_present": 1.5, "face_sharp": 2, "face_quality": 1.5,
               "eyes_open": 2, "mouth_closed": 1, "frontal": 1, "face_complete": 1.5, "composition": 1.5,
               "aesthetic": 1.5, "no_text": 1},
    "contact": {"sharp": 2, "still": 1.5, "exposure": 1, "focus_stable": 0.5, "representative": 3, "eyes_open": 1,
                "face_complete": 0.5, "no_text": 0.5},
}
# Rasgos con significado absoluto 0..1: no se rankean, así una cara con los ojos cerrados resta aunque sea la única
# del plano, y un 0,01 % de píxeles quemados no cuesta el peso entero.
ABSOLUTE = {"exposure", "face_present", "face_quality", "eyes_open", "mouth_closed", "frontal", "face_complete",
            "composition", "aesthetic", "no_text"}
EDGE = 0.10        # criterio 5: fuera el primer y el último 10 % del plano
CANDIDATES = 8     # candidatos por plano que pasan a la segunda pasada
# D19. shortcut: umbrales a ojo hasta la prueba con el owner
FRAMING_DIFF = 0.10    # diferencia media de la miniatura 16x9 a partir de la cual es «otro encuadre»
MIN_SHOT = 12          # frames: un plano más corto no da still (con mínimo 0)
SHARP_GATE = 0.30      # el mejor frame por debajo del 30 % de la nitidez mediana del timeline no da still


def rank(values):
    """Rango percentil 0..1 dentro del plano (None se conserva). Empates → mismo rango."""
    idx = [i for i, v in enumerate(values) if v is not None]
    out = [None] * len(values)
    if not idx:
        return out
    vals = np.array([values[i] for i in idx], dtype=float)
    if len(idx) == 1 or np.ptp(vals) == 0:
        for i in idx:
            out[i] = 0.5
        return out
    order = vals.argsort().argsort()
    r = order / (len(idx) - 1)
    # empates: media de sus rangos
    for v in np.unique(vals):
        same = vals == v
        r[same] = r[same].mean()
    for k, i in enumerate(idx):
        out[i] = float(r[k])
    return out


def valid_mask(metrics):
    """Criterio 5: bordes del plano, frames negros y flashes/fundidos fuera. Si no queda nada, se usan todos."""
    n = len(metrics)
    edge = int(n * EDGE)
    lumas = [m["luma"] for m in metrics]
    med = float(np.median(lumas))

    def spike(i):
        # flash o frame negro: salta respecto a sus dos vecinos, que se parecen entre sí. Una rampa (iris) no es un pico.
        if 0 < i < n - 1:
            a, b = lumas[i - 1], lumas[i + 1]
            return abs(lumas[i] - (a + b) / 2) > 0.08 and abs(a - b) < 0.04
        return False

    ok = [edge <= i < n - edge and not spike(i) and not (med > 0.1 and lumas[i] < 0.02) for i in range(n)]
    return ok if any(ok) else [True] * n


def cheap_features(metrics):
    """Rasgos de la primera pasada, ya rankeados dentro del plano (solo sobre los frames válidos)."""
    ok = valid_mask(metrics)
    sel = [m if v else None for m, v in zip(metrics, ok)]
    sharp = [m["sharp"] if m else None for m in sel]
    # criterio 4 (rack focus): se prefiere donde la nitidez ya se ha asentado, no donde cambia
    unstable = [None] * len(sel)
    for i, m in enumerate(sel):
        if m:
            near = [metrics[j]["sharp"] for j in (i - 1, i + 1) if 0 <= j < len(metrics)]
            unstable[i] = max(abs(m["sharp"] - s) for s in near) / (m["sharp"] + 1e-6) if near else 0.0
    thumbs = np.array([m["thumb"] for m in metrics])
    mean_thumb = thumbs[np.array(ok)].mean(0)
    feats = {
        "sharp": rank(sharp),
        "still": rank([-m["motion"] if m and m["motion"] is not None else None for m in sel]),
        # 20 % del cuadro quemado o empastado = 0
        "exposure": [1 - min(m["clipped"] / 0.2, 1.0) if m else None for m in sel],
        "focus_stable": rank([-u if u is not None else None for u in unstable]),
        "tonal": rank([m["tonal"] if m else None for m in sel]),
        # sin piel en el plano no hay señal: no se rankea un plano entero a cero
        "skin": rank([m["skin"] if m and max(x["skin"] for x in metrics) > 0.01 else None for m in sel]),
        "representative": rank([-float(np.abs(m["thumb"] - mean_thumb).mean()) if m else None for m in sel]),
    }
    return [{k: v[i] for k, v in feats.items()} for i in range(len(metrics))], ok


def face_features(analysis, face_sharp=None):
    """Rasgos de la segunda pasada para un candidato, a partir de faces.analyze(); sin cara, todo None (no resta)."""
    text, aes = analysis.get("text_fraction"), analysis.get("aesthetic")
    out = {"no_text": None if text is None else 1 - min(text / 0.05, 1.0),  # 5 % del cuadro con texto = 0
           "aesthetic": None if aes is None else (aes + 1) / 2,           # Vision da −1..1
           "composition": _composition(analysis.get("saliency_box"))}
    faces = analysis.get("faces") or []
    if faces:
        f = max(faces, key=lambda f: f["box"][2] * f["box"][3])  # la cara principal es la más grande
        mouth, yaw = f.get("mouth_open"), f.get("yaw")
        out.update({
            "face_present": 1.0,
            "face_sharp": face_sharp,
            "face_quality": f.get("quality"),
            "eyes_open": f.get("eyes_open"),
            # shortcut: boca cerrada ≈ 0,05 y abierta ≈ 0,35 (alto/ancho de los labios); a ajustar con caras reales
            "mouth_closed": None if mouth is None else 1 - min(max((mouth - 0.05) / 0.3, 0.0), 1.0),
            # el perfil no hunde el frame (es lo que da el plano): frontal 1, perfil 0,5
            "frontal": None if yaw is None else 1 - min(abs(yaw), 90.0) / 180,
            "face_complete": 0.0 if f.get("cut") else 1.0,
        })
    return out


def _composition(box):
    """Criterio 12: sujeto principal sin cortar por el borde y cerca de una intersección de tercios."""
    if not box:
        return None
    x, y, w, h = box
    cut = x <= 0.01 or y <= 0.01 or x + w >= 0.99 or y + h >= 0.99
    cx, cy = x + w / 2, y + h / 2
    d = min(np.hypot(cx - tx, cy - ty) for tx in (1 / 3, 2 / 3) for ty in (1 / 3, 2 / 3))
    return (0.0 if cut else 0.5) + 0.5 * (1 - min(d / 0.5, 1.0))


def score(feats, weights):
    """Media ponderada de los rasgos disponibles en cada frame. Los rasgos continuos se rankean entre los frames dados."""
    keys = [k for k in weights if any(f.get(k) is not None for f in feats)]
    ranked = {k: ([f.get(k) for f in feats] if k in ABSOLUTE else rank([f.get(k) for f in feats])) for k in keys}
    out = []
    for i in range(len(feats)):
        num = den = 0.0
        for k in keys:
            v = ranked[k][i]
            if v is not None:
                num += weights[k] * v
                den += weights[k]
        out.append(num / den if den else 0.0)
    return out


def pick(frames, scores, thumbs, n, min_gap=None, min_diff=0.03):
    """Criterio 18: los n mejores con separación en tiempo (min_gap frames) y en contenido (miniatura)."""
    if min_gap is None:
        span = (max(frames) - min(frames) + 1) if frames else 0
        min_gap = max(3, span // (2 * max(n, 1)))
    chosen = []
    order = sorted(range(len(frames)), key=lambda i: -scores[i])
    # en un plano estático todo se parece: si no salen n distintos en contenido, basta con separarlos en tiempo
    for diff in (min_diff, 0.0):
        for i in order:
            if len(chosen) == n:
                return chosen
            if i not in chosen and all(abs(frames[i] - frames[j]) >= min_gap
                                       and np.abs(thumbs[i] - thumbs[j]).mean() >= diff for j in chosen):
                chosen.append(i)
    return chosen


def framings(thumbs, ok):
    """D19: tramos de encuadre a lo largo del plano. Uno nuevo empieza cuando la composición se aleja lo bastante
    del primer frame del tramo (la cámara se ha movido). Un tramo demasiado corto se une al anterior."""
    idx = [i for i, v in enumerate(ok) if v]
    min_len = max(6, len(idx) // 8)
    segs = []
    for i in idx:
        if segs and np.abs(thumbs[i] - thumbs[segs[-1][0]]).mean() <= FRAMING_DIFF:
            segs[-1].append(i)
        elif segs and len(segs[-1]) < min_len:
            segs[-1].append(i)  # el tramo anterior aún es un barrido, no un encuadre: se alarga
        else:
            segs.append([i])
    if len(segs) > 1 and len(segs[-1]) < min_len:
        segs[-2] += segs.pop()
    return segs
