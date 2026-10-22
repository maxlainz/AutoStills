"""Métricas baratas por frame (criterios A y D de docs/criterios.md). Todo en numpy/OpenCV, sin modelos."""
import cv2
import numpy as np

WORK_WIDTH = 640  # las métricas globales no necesitan más; las caras sí (faces.py va a resolución completa)


def _gray_small(img_bgr):
    h, w = img_bgr.shape[:2]
    if w > WORK_WIDTH:
        img_bgr = cv2.resize(img_bgr, (WORK_WIDTH, round(h * WORK_WIDTH / w)), interpolation=cv2.INTER_AREA)
    return img_bgr, cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def sharpness(gray, box=None):
    """Varianza del laplaciano (criterio 1); `box` normalizado (x, y, w, h) para medir solo en la cara o la zona saliente."""
    if box:
        h, w = gray.shape
        x0, y0 = int(box[0] * w), int(box[1] * h)
        x1, y1 = max(x0 + 2, int((box[0] + box[2]) * w)), max(y0 + 2, int((box[1] + box[3]) * h))
        gray = gray[max(0, y0):min(h, y1), max(0, x0):min(w, x1)]
        if min(gray.shape) < 3:  # caja fuera del cuadro o diminuta: no hay medida (no resta)
            return None
    return float(cv2.Laplacian(gray, cv2.CV_64F, ksize=3).var())


def camera_step(prev_gray, gray):
    """Movimiento de cámara entre dos frames → (escala, dx, dy), desplazamiento en anchos de cuadro. Flujo óptico de
    puntos de toda la imagen con RANSAC: manda el fondo, no lo que hacen los actores (D19, bitácora 03)."""
    p0 = cv2.goodFeaturesToTrack(prev_gray, 300, 0.01, 8)
    if p0 is None or len(p0) < 12:
        return 1.0, 0.0, 0.0
    p1, st, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, p0, None)
    ok = st.ravel() == 1
    if ok.sum() < 12:
        return 1.0, 0.0, 0.0
    m, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
    if m is None:
        return 1.0, 0.0, 0.0
    w = prev_gray.shape[1]
    return float(np.hypot(m[0, 0], m[1, 0])), float(m[0, 2]) / w, float(m[1, 2]) / w


def frame_metrics(img_bgr, prev_gray=None):
    """Devuelve (métricas, gray) — `gray` se pasa como `prev_gray` al frame siguiente para medir movimiento."""
    small, gray = _gray_small(img_bgr)
    luma = gray / 255.0
    ycrcb = cv2.cvtColor(small, cv2.COLOR_BGR2YCrCb)
    # shortcut: rango YCrCb clásico de piel; con grades muy fuertes falla, revisar con la prueba de pesos
    skin = cv2.inRange(ycrcb, (40, 135, 85), (240, 180, 135))
    p2, p98 = np.percentile(luma, (2, 98))
    m = {
        "sharp": sharpness(gray),
        "motion": None if prev_gray is None or prev_gray.shape != gray.shape
        else float(np.abs(gray.astype(np.int16) - prev_gray).mean() / 255.0),
        "luma": float(luma.mean()),
        "clipped": float((gray > 250).mean() + (gray < 5).mean()),
        "tonal": float(p98 - p2),
        "skin": float((skin > 0).mean()),
        "cam": (1.0, 0.0, 0.0) if prev_gray is None or prev_gray.shape != gray.shape else camera_step(prev_gray, gray),
        # miniatura 16x9 en color: sirve para «representativo del plano» (14) y para la diversidad (18)
        "thumb": cv2.resize(small, (16, 9), interpolation=cv2.INTER_AREA).astype(np.float32).ravel() / 255.0,
    }
    return m, gray


def difference(img_a, img_b):
    """Diferencia media absoluta 0..1 entre dos imágenes a 160 px: decide si el export cuadra con Resolve (D17).
    Un grade cambiado, un flat pass o un plano distinto dan valores altos; la compresión del render, valores bajos."""
    a = cv2.resize(img_a, (160, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
    b = cv2.resize(img_b, (160, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
    return float(np.abs(a - b).mean() / 255.0)
