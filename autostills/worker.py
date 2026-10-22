"""Worker de AutoStills: `python -m autostills.worker job.json result.json`.

Corre con el entorno de uv que crea install.command (D11), nunca dentro de Resolve (norma resolve.md).
Escribe el progreso en stdout, una línea JSON por plano, para la barra de la ventana.

job.json:
  {"source": "video", "video": "<ruta del export>", "video_first_frame": <frame de timeline del frame 0 del vídeo>,
   | "source": "frames", "frames": {"<frame de timeline>": "<ruta de imagen>", ...},   # muestreo desde Resolve (D13)
   "shots": [{"id": "...", "start": <frame>, "end": <frame, exclusivo>}, ...],
   "preset": "gallery" | "social" | "contact", "n": 1, "aesthetics": false}
result.json:
  {"version": "...", "shots": [{"id", "analysed": <frames>, "flags": [...],
                                "picks": [{"frame": <frame de timeline>, "score": 0..1, "detail": {rasgo: valor}}]}]}
"""
import json
import sys

import cv2
import numpy as np

from . import __version__, faces, metrics, select

CHEAP = ("sharp", "still", "exposure", "focus_stable", "tonal", "skin", "representative")


def analyse_shot(frames, images, preset="gallery", n=1, aesthetics=False):
    """`frames`: frames de timeline en orden; `images`: función frame → imagen BGR a resolución completa."""
    weights = select.PRESETS[preset]
    mets, prev, readable = [], None, []
    for f in frames:
        img = images(f)
        if img is None:  # fichero que falta o ilegible: se salta y se avisa, no tumba el plano
            continue
        m, prev = metrics.frame_metrics(img, prev)
        mets.append(m)
        readable.append(f)
    lost = len(frames) - len(readable)
    frames = readable
    if not frames:
        return {"analysed": 0, "flags": ["sin_frames"], "picks": []}
    feats, ok = select.cheap_features(mets)
    idx = [i for i, v in enumerate(ok) if v]
    cheap_w = {k: w for k, w in weights.items() if k in CHEAP}
    cheap = select.score([feats[i] for i in idx], cheap_w)
    cand = [idx[j] for j in select.pick([frames[i] for i in idx], cheap, [mets[i]["thumb"] for i in idx],
                                        max(select.CANDIDATES, n))]
    any_face = False
    for i in cand:
        img = images(frames[i])
        a = faces.analyze(img, aesthetics=aesthetics) if faces.available() else {"faces": []}
        box = max(a["faces"], key=lambda f: f["box"][2] * f["box"][3])["box"] if a.get("faces") else None
        any_face |= box is not None
        face_sharp = metrics.sharpness(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), box) if box else None
        feats[i] = {**feats[i], **select.face_features(a, face_sharp)}
    final = select.score([feats[i] for i in cand], weights)
    picks = select.pick([frames[i] for i in cand], final, [mets[i]["thumb"] for i in cand], n)
    flags = [] if any_face or not faces.available() else ["sin_cara"]
    if not faces.available():
        flags.append("sin_vision")
    if len(frames) < 3:
        flags.append("plano_corto")
    if lost:
        flags.append(f"frames_ilegibles:{lost}")
    return {"analysed": len(frames), "flags": flags,
            "picks": [{"frame": frames[cand[j]], "score": round(final[j], 4),
                       "detail": {k: (round(v, 4) if isinstance(v, float) else v)
                                  for k, v in feats[cand[j]].items() if v is not None}} for j in picks]}


def _video_shots(job, shots):
    """Lee el export una sola vez, en orden. Guarda en JPEG los frames del plano en curso para la segunda pasada."""
    cap = cv2.VideoCapture(job["video"])
    if not cap.isOpened():
        raise SystemExit(f"No se puede abrir el export: {job['video']}")
    first = job["video_first_frame"]
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    pending = sorted(shots, key=lambda s: s["start"])
    buf, i, fails = {}, 0, 0
    while pending:
        ok, img = cap.read()
        f = first + i
        i += 1
        fails = 0 if ok else fails + 1
        # un frame corrupto a mitad del export no corta la lectura; el final de verdad sí
        eof = not ok and (fails > 5 or i > total)
        if ok and any(s["start"] <= f < s["end"] for s in pending):
            # shortcut: un plano muy largo ocupa ~250 KB por frame en memoria; leer dos veces si llega a molestar
            buf[f] = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])[1]
        for s in [s for s in pending if eof or f >= s["end"] - 1]:
            pending.remove(s)
            fr = [x for x in range(s["start"], s["end"]) if x in buf]
            yield s, fr, (lambda x: cv2.imdecode(buf[x], cv2.IMREAD_COLOR))
            for x in fr:
                if not any(p["start"] <= x < p["end"] for p in pending):
                    buf.pop(x, None)
        if eof:
            break
    cap.release()


def _frame_shots(job, shots):
    paths = {int(k): v for k, v in job["frames"].items()}
    for s in shots:
        fr = sorted(f for f in paths if s["start"] <= f < s["end"])
        yield s, fr, (lambda x: cv2.imread(paths[x], cv2.IMREAD_COLOR))  # None si falta: analyse_shot lo salta


def run(job):
    shots = job["shots"]
    gen = _video_shots(job, shots) if job["source"] == "video" else _frame_shots(job, shots)
    out = []
    for k, (s, fr, images) in enumerate(gen, 1):
        try:
            res = analyse_shot(fr, images, job.get("preset", "gallery"), job.get("n", 1), job.get("aesthetics", False))
        except Exception as e:  # un plano raro no se lleva por delante el resto del timeline
            res = {"analysed": 0, "flags": [f"error:{type(e).__name__}: {e}"], "picks": []}
        out.append({"id": s["id"], **res})
        print(json.dumps({"progress": k / len(shots), "shot": s["id"]}), flush=True)
    order = {s["id"]: i for i, s in enumerate(shots)}
    return {"version": __version__, "shots": sorted(out, key=lambda r: order[r["id"]])}


def _jsonable(o):
    return o.item() if isinstance(o, np.generic) else str(o)


if __name__ == "__main__":
    job_path, result_path = sys.argv[1], sys.argv[2]
    with open(job_path) as fh:
        result = run(json.load(fh))
    with open(result_path, "w") as fh:
        json.dump(result, fh, indent=1, default=_jsonable)
