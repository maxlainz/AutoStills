"""Puntuación sobre frames sintéticos: nada de material real (norma repo-publico.md)."""
import json
import tomllib
from pathlib import Path

import cv2
import numpy as np

import autostills
from autostills import metrics, select, worker

ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(0)
PATTERN = (RNG.random((540, 960, 3)) * 255).astype(np.uint8)
PATTERN = cv2.resize(cv2.resize(PATTERN, (240, 135)), (960, 540), interpolation=cv2.INTER_NEAREST)  # bloques nítidos


def blurred(sigma):
    return PATTERN.copy() if sigma == 0 else cv2.GaussianBlur(PATTERN, (0, 0), sigma)


def test_version_matches_pyproject():
    import AutoStills
    v = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert autostills.__version__ == AutoStills.__version__ == v


def test_sharpness_and_motion():
    sharp, _ = metrics.frame_metrics(blurred(0))
    soft, gray = metrics.frame_metrics(blurred(3))
    assert sharp["sharp"] > 5 * soft["sharp"]
    same, _ = metrics.frame_metrics(blurred(3), gray)
    assert same["motion"] == 0.0 and soft["motion"] is None


def test_exposure_and_difference():
    burnt = np.clip(PATTERN.astype(int) * 3, 0, 255).astype(np.uint8)
    assert metrics.frame_metrics(burnt)[0]["clipped"] > metrics.frame_metrics(PATTERN)[0]["clipped"] + 0.3
    flat = (PATTERN * 0.4 + 90).astype(np.uint8)  # como un flat pass: misma imagen, sin contraste
    jpeg = cv2.imdecode(cv2.imencode(".jpg", PATTERN, [cv2.IMWRITE_JPEG_QUALITY, 80])[1], cv2.IMREAD_COLOR)
    assert metrics.difference(PATTERN, jpeg) < 0.02 < 0.05 < metrics.difference(PATTERN, flat)


def test_rank_ties_and_none():
    assert select.rank([1, None, 3, 3]) == [0.0, None, 0.75, 0.75]
    assert select.rank([None, 2]) == [None, 0.5]


def test_valid_mask_drops_edges_and_flash():
    lumas = [0.4] * 20
    lumas[10] = 0.95  # flash
    lumas[6] = 0.0    # frame negro
    ok = select.valid_mask([{"luma": v} for v in lumas])
    assert ok[:2] == [False, False] and ok[-2:] == [False, False] and not ok[10] and not ok[6] and ok[5]


def test_valid_mask_keeps_a_ramp():
    ok = select.valid_mask([{"luma": 0.2 + 0.03 * i} for i in range(20)])  # iris abriéndose: no es un flash
    assert all(ok[2:18])


def test_pick_keeps_distance():
    frames = list(range(10))
    thumbs = [np.full(3, i / 10) for i in frames]
    scores = [0.1, 0.2, 0.9, 0.85, 0.3, 0.2, 0.1, 0.8, 0.1, 0.0]
    assert select.pick(frames, scores, thumbs, 2, min_gap=3) == [2, 7]


def test_signal_that_does_not_apply_does_not_subtract():
    w = {"sharp": 1, "eyes_open": 1}
    s = select.score([{"sharp": 0.9}, {"sharp": 0.1, "eyes_open": 0.9}], w)
    assert s[0] == 1.0  # sin cara: solo cuenta la nitidez, ranking 1.0


def _write_video(path, imgs, fps=25):
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (imgs[0].shape[1], imgs[0].shape[0]))
    for im in imgs:
        vw.write(im)
    vw.release()


def test_worker_picks_sharpest_frame_from_video(tmp_path):
    # plano A (frames 1000–1029): un pase de foco que clava en el 1017; plano B (1030–1059): quemado salvo una ventana
    # bien expuesta del 1042 al 1046
    a = [blurred(0.4 * abs(i - 17)) for i in range(30)]
    gray = cv2.cvtColor(cv2.normalize(cv2.cvtColor(PATTERN, cv2.COLOR_BGR2GRAY), None, 0, 235, cv2.NORM_MINMAX),
                        cv2.COLOR_GRAY2BGR)
    b = [np.clip(gray.astype(int) + (0 if abs(i - 14) <= 2 else 90), 0, 255).astype(np.uint8) for i in range(30)]
    _write_video(tmp_path / "export.avi", a + b)
    job = {"source": "video", "video": str(tmp_path / "export.avi"), "video_first_frame": 1000,
           "shots": [{"id": "A", "start": 1000, "end": 1030}, {"id": "B", "start": 1030, "end": 1060}],
           "preset": "gallery"}
    res = worker.run(job)
    picks = {s["id"]: [p["frame"] for p in s["picks"]] for s in res["shots"]}
    assert picks["A"] == [1017] and 1042 <= picks["B"][0] <= 1046
    assert all(s["analysed"] == 30 for s in res["shots"])


def test_worker_frames_source_and_n(tmp_path):
    frames = {}
    for k, f in enumerate(range(2000, 2100, 5)):  # 20 muestras de un plano, como el muestreo desde Resolve
        p = tmp_path / f"{f}.png"
        cv2.imwrite(str(p), blurred(0 if k in (6, 14) else 3))
        frames[str(f)] = str(p)
    job = {"source": "frames", "frames": frames, "shots": [{"id": "S", "start": 2000, "end": 2100}], "min": 2, "max": 2}
    res = json.loads(json.dumps(worker.run(job), default=worker._jsonable))
    assert sorted(p["frame"] for p in res["shots"][0]["picks"]) == [2030, 2070]


def test_missing_frame_is_skipped_not_fatal(tmp_path):
    p = tmp_path / "ok.png"
    cv2.imwrite(str(p), PATTERN)
    job = {"source": "frames", "frames": {"5": "/no/existe.png", "6": str(p)},
           "shots": [{"id": "x", "start": 0, "end": 10}, {"id": "y", "start": 10, "end": 20}], "min": 1}
    res = {s["id"]: s for s in worker.run(job)["shots"]}
    assert [p["frame"] for p in res["x"]["picks"]] == [6] and "frames_ilegibles:1" in res["x"]["flags"]
    assert res["y"]["flags"] == ["sin_frames"]


def test_n_above_candidates(tmp_path):
    imgs = [blurred(i % 4) for i in range(60)]
    res = worker.analyse_shot(list(range(60)), lambda f: imgs[f], min_n=12, max_n=12)
    assert len(res["picks"]) == 12


def test_bad_face_scores_below_good_face():
    good = select.face_features({"faces": [{"box": (0.3, 0.3, 0.2, 0.2), "quality": 0.8, "eyes_open": 1.0,
                                            "mouth_open": 0.05, "yaw": 0.0, "cut": False}], "text_fraction": 0.0})
    bad = select.face_features({"faces": [{"box": (0.3, 0.3, 0.2, 0.2), "quality": 0.1, "eyes_open": 0.0,
                                           "mouth_open": 0.4, "yaw": 0.0, "cut": False}], "text_fraction": 0.0})
    w = {k: v for k, v in select.PRESETS["gallery"].items() if k not in ("face_sharp",)}
    # sola en su plano, la cara mala sigue puntuando bajo: los rasgos absolutos no se rankean
    assert select.score([bad], w)[0] < 0.6 < select.score([good], w)[0]


def test_sharpness_box_outside_frame():
    assert metrics.sharpness(cv2.cvtColor(PATTERN, cv2.COLOR_BGR2GRAY), (1.2, 0.2, 0.1, 0.1)) is None


def test_check_and_mixed_sources(tmp_path):
    # export de 20 frames; el frame 105 de Resolve ya no cuadra (grade cambiado después del render)
    imgs = [blurred(0.3 * abs(i - 8)) for i in range(20)]
    _write_video(tmp_path / "e.avi", imgs)
    now = {}
    for f, im in ((102, imgs[2]), (105, (imgs[5] * 0.4 + 90).astype(np.uint8))):
        cv2.imwrite(str(tmp_path / f"{f}.png"), im)
        now[str(f)] = str(tmp_path / f"{f}.png")
    d = worker.run({"source": "check", "video": str(tmp_path / "e.avi"), "video_first_frame": 100, "frames": now})["diff"]
    assert d["102"] < 0.02 and d["105"] > 0.05
    # mezcla: el plano A sale del export, el B de sus frames muestreados
    sampled = {str(f): str(tmp_path / f"{f}.png") for f in (115, 116)}
    cv2.imwrite(sampled["115"], blurred(3))
    cv2.imwrite(sampled["116"], blurred(0))
    job = {"source": "video", "video": str(tmp_path / "e.avi"), "video_first_frame": 100,
           "shots": [{"id": "A", "start": 100, "end": 110}, {"id": "B", "start": 110, "end": 120, "frames": sampled}],
           "min": 1, "max": 1}
    res = {s["id"]: s for s in worker.run(job)["shots"]}
    assert res["A"]["analysed"] == 10 and [p["frame"] for p in res["A"]["picks"]] == [108]
    assert res["B"]["analysed"] == 2 and [p["frame"] for p in res["B"]["picks"]] == [116]


def test_two_framings_give_two_stills():
    def scene(x):  # textura con un objeto grande y claro en la posición x: la cámara ha cambiado de encuadre
        im = (PATTERN // 3).copy()
        im[100:440, x:x + 300] = np.clip(PATTERN[100:440, x:x + 300].astype(int) + 140, 0, 255)
        return im
    left, right = scene(60), scene(600)
    imgs = [cv2.GaussianBlur(left, (0, 0), 0.3 * abs(i - 12) + 0.01) for i in range(30)] + \
           [cv2.GaussianBlur(right, (0, 0), 0.3 * abs(i - 45) + 0.01) for i in range(30, 60)]
    res = worker.analyse_shot(list(range(60)), lambda f: imgs[f], max_n=3)
    assert res["framings"] == 2 and sorted(p["frame"] for p in res["picks"]) == [12, 45]
    assert len(worker.analyse_shot(list(range(60)), lambda f: imgs[f], max_n=1)["picks"]) == 1


def test_gate_drops_short_and_soft_shots():
    res = [{"id": i, "picks": [{"frame": 1}], "flags": [], "best_sharp": v}
           for i, v in (("a", 900.0), ("b", 1000.0), ("c", 1100.0), ("soft", 100.0), ("short", 1000.0))]
    worker._gate(res, {"a": 50, "b": 50, "c": 50, "soft": 50, "short": 8})
    kept = {r["id"]: bool(r["picks"]) for r in res}
    assert kept == {"a": True, "b": True, "c": True, "soft": False, "short": False}
    assert "descartado:blando" in res[3]["flags"] and "descartado:corto" in res[4]["flags"]
