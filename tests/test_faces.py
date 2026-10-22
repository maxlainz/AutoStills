"""faces.py: helpers puros en cualquier plataforma; Vision solo en macOS. Sin fotos reales (norma repo-publico.md)."""
import time

import cv2
import numpy as np
import pytest

from autostills import faces


def ellipse(w, h, n=8):
    return [(w / 2 * np.cos(t), h / 2 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]


def test_aspect_ratio_open_vs_closed():
    open_eye, closed_eye = faces.aspect_ratio(ellipse(30, 12)), faces.aspect_ratio(ellipse(30, 2))
    assert open_eye == pytest.approx(0.4, abs=0.01)
    assert closed_eye < open_eye
    assert faces.eye_open_score(open_eye) == 1.0
    assert faces.eye_open_score(closed_eye) == 0.0


def test_aspect_ratio_ignores_roll():
    pts = ellipse(30, 12)
    a = np.radians(35)
    rolled = [(x * np.cos(a) - y * np.sin(a), x * np.sin(a) + y * np.cos(a)) for x, y in pts]
    assert faces.aspect_ratio(rolled) == pytest.approx(faces.aspect_ratio(pts), abs=0.01)


def test_aspect_ratio_degenerate():
    assert faces.aspect_ratio([(0, 0), (1, 1)]) is None
    assert faces.aspect_ratio([(1, 1)] * 4) is None
    assert faces.eye_open_score(None) is None


def test_mouth_open_vs_closed():
    assert faces.aspect_ratio(ellipse(50, 25)) > faces.aspect_ratio(ellipse(50, 1))


def test_to_top_left():
    assert faces.to_top_left((0.1, 0.2, 0.3, 0.4)) == pytest.approx((0.1, 0.4, 0.3, 0.4))


def test_is_cut():
    assert not faces.is_cut((0.3, 0.3, 0.2, 0.2))
    assert faces.is_cut((0.0, 0.3, 0.2, 0.2))
    assert faces.is_cut((0.85, 0.3, 0.15, 0.2))
    assert faces.is_cut((0.3, 0.9, 0.2, 0.2))


def test_analyze_without_vision(monkeypatch):
    monkeypatch.setattr(faces, "Vision", None)
    assert faces.analyze(np.zeros((10, 10, 3), np.uint8)) == faces.empty_result()


vision = pytest.mark.skipif(not faces.available(), reason="Vision solo existe en macOS")


@vision
def test_noise_has_no_faces_nor_text():
    img = np.random.default_rng(0).integers(0, 256, (540, 960, 3), dtype=np.uint8)
    r = faces.analyze(img)
    assert r["faces"] == [] and r["text_fraction"] == 0.0 and r["aesthetic"] is None


@vision
def test_rendered_text_is_detected():
    img = np.full((540, 960, 3), 80, np.uint8)
    cv2.putText(img, "SAMPLE TEXT", (40, 300), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 8)
    assert faces.analyze(img)["text_fraction"] > 0


@vision
def test_analyze_speed_and_aesthetics():
    img = np.full((1080, 1600, 3), 120, np.uint8)
    faces.analyze(img, aesthetics=True)  # la primera llamada carga los modelos
    t = time.perf_counter()
    r = faces.analyze(img, aesthetics=True)
    ms = (time.perf_counter() - t) * 1000
    print(f"analyze 1600x1080 con estética: {ms:.0f} ms")
    assert ms < 1000
    assert r["aesthetic"] is None or -1.0 <= r["aesthetic"] <= 1.0
