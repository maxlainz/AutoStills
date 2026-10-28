"""Señales de Apple Vision para un frame: caras (criterios 6-11), saliencia (12), estética (13) y texto (20).

Corre en el worker, nunca en la GUI de Resolve (norma resolve.md). En Linux (CI) Vision no existe:
`available()` es False y `analyze()` devuelve el resultado vacío.
"""

import math
import sys

import cv2
import numpy as np

try:
    import objc
    import Vision
    from Foundation import NSData, NSDictionary
except ImportError:  # Linux / sin pyobjc
    Vision = None

# Apertura del ojo (alto/ancho del contorno). Vision nunca colapsa del todo el contorno de un ojo cerrado,
# así que ~0.10 se toma como cerrado y ~0.25 como claramente abierto; entre medias, lineal.
EAR_CLOSED = 0.10
EAR_OPEN = 0.25
CUT_MARGIN = 0.01


def available():
    return sys.platform == "darwin" and Vision is not None


def empty_result():
    return {"faces": [], "saliency_box": None, "aesthetic": None, "text_fraction": None}  # None = Vision no respondió; no resta


def aspect_ratio(points):
    """Alto/ancho de un contorno (ojo o labios), medido sobre su propio eje para que el roll no cuente."""
    p = np.asarray(points, dtype=float)
    if len(p) < 3:
        return None
    d = np.linalg.norm(p[:, None] - p[None], axis=2)
    i, j = np.unravel_index(d.argmax(), d.shape)
    width = d[i, j]
    if width == 0:
        return None
    axis = (p[j] - p[i]) / width
    perp = p @ np.array([-axis[1], axis[0]])
    return float((perp.max() - perp.min()) / width)


def eye_open_score(ear):
    if ear is None:
        return None
    return float(np.clip((ear - EAR_CLOSED) / (EAR_OPEN - EAR_CLOSED), 0.0, 1.0))


def to_top_left(box):
    """Caja normalizada de Vision (origen abajo-izquierda) a origen arriba-izquierda."""
    x, y, w, h = box
    return (x, 1.0 - y - h, w, h)


def is_cut(box, margin=CUT_MARGIN):
    x, y, w, h = box
    return x < margin or y < margin or x + w > 1 - margin or y + h > 1 - margin


def _rect(r):
    return (r.origin.x, r.origin.y, r.size.width, r.size.height)


def _points(region, size):
    if region is None:
        return None
    pts = region.pointsInImageOfSize_(size)  # píxeles: el normalizado a la caja de la cara deforma el aspecto
    return [(pts[k].x, pts[k].y) for k in range(region.pointCount())]


def _angle(value):
    return None if value is None else math.degrees(float(value))


def _perform(handler, requests):
    ok, _err = handler.performRequests_error_(requests, None)
    return ok


def analyze(img_bgr, aesthetics=False):
    """Analiza un frame BGR uint8. Nunca lanza: una petición que falla deja su campo en None."""
    out = empty_result()
    if not available():
        return out
    h, w = img_bgr.shape[:2]
    size = (w, h)
    try:
        with objc.autorelease_pool():
            ok, buf = cv2.imencode(".bmp", img_bgr)  # BMP: sin compresión, lo más rápido de codificar
            if not ok:
                return out
            # H16: opciones como NSDictionary; con un `{}` de Python, macOS 27 lanza «key does not exist»
            handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
                NSData.dataWithBytes_length_(buf, len(buf)), NSDictionary.dictionary())
            landmarks = Vision.VNDetectFaceLandmarksRequest.alloc().init()
            saliency = Vision.VNGenerateAttentionBasedSaliencyImageRequest.alloc().init()
            text = Vision.VNDetectTextRectanglesRequest.alloc().init()
            reqs = [landmarks, saliency, text]
            aes = None
            if aesthetics and hasattr(Vision, "VNCalculateImageAestheticsScoresRequest"):
                aes = Vision.VNCalculateImageAestheticsScoresRequest.alloc().init()
                reqs.append(aes)
            # Cada petición por separado: si una falla, las demás siguen.
            done = {id(r): _perform(handler, [r]) for r in reqs}

            obs = list(landmarks.results() or [])
            quality = [None] * len(obs)
            if obs:
                q = Vision.VNDetectFaceCaptureQualityRequest.alloc().init()
                q.setInputFaceObservations_(obs)
                if _perform(handler, [q]):
                    qres = list(q.results() or [])
                    if len(qres) == len(obs):
                        quality = [None if r.faceCaptureQuality() is None else float(r.faceCaptureQuality()) for r in qres]

            for o, qual in zip(obs, quality):
                box = to_top_left(_rect(o.boundingBox()))
                lm = o.landmarks()
                eyes = mouth = None
                if lm is not None:
                    ears = [aspect_ratio(p) for p in (_points(lm.leftEye(), size), _points(lm.rightEye(), size)) if p]
                    ears = [e for e in ears if e is not None]
                    eyes = eye_open_score(sum(ears) / len(ears)) if ears else None
                    lips = _points(lm.innerLips(), size) or _points(lm.outerLips(), size)
                    mouth = aspect_ratio(lips) if lips else None
                out["faces"].append({
                    "box": box,
                    "quality": qual,
                    "eyes_open": eyes,
                    "mouth_open": mouth,
                    "yaw": _angle(o.yaw()),
                    "cut": is_cut(box),
                })

            sal = saliency.results()
            objs = list(sal[0].salientObjects() or []) if sal else []
            if objs:
                rs = [_rect(s.boundingBox()) for s in objs]
                x0, y0 = min(r[0] for r in rs), min(r[1] for r in rs)
                x1, y1 = max(r[0] + r[2] for r in rs), max(r[1] + r[3] for r in rs)
                out["saliency_box"] = to_top_left((x0, y0, x1 - x0, y1 - y0))

            if aes is not None and aes.results():
                out["aesthetic"] = float(aes.results()[0].overallScore())

            # Las cajas de texto pueden solaparse: se pinta una máscara en vez de sumar áreas.
            if done[id(text)]:
                mask = np.zeros((h, w), np.uint8)
                for b in list(text.results() or []):
                    x, y, bw, bh = to_top_left(_rect(b.boundingBox()))
                    # una caja que asoma por arriba o por la izquierda daría un índice negativo: se recorta a 0
                    mask[max(0, int(y * h)):int(math.ceil((y + bh) * h)), max(0, int(x * w)):int(math.ceil((x + bw) * w))] = 1
                out["text_fraction"] = float(mask.mean())
    except Exception as e:  # un frame raro no puede tumbar el análisis de un timeline entero, pero se avisa (H16)
        out["error"] = f"{type(e).__name__}: {e}"
    return out
