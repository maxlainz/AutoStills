"""Lógica pura de la ventana (AutoStills.py), sin Resolve."""
import AutoStills as A


def item(track, start, end, path="a.mov", src=0, markers=None, name="clip.mov"):
    return {"track": track, "start": start, "end": end, "path": path, "src": src, "markers": markers or {},
            "name": name, "uid": f"{track}-{start}"}


def test_tc():
    assert A.tc(90000, 25) == "01:00:00:00" and A.tc(90217, 25.0) == "01:00:08:17" and A.tc(86400 + 23, 23.976) == "01:00:00:23"


def test_upper_track_covers_lower():
    shots = A.visible_shots([item(1, 0, 100, "a"), item(2, 30, 50, "b"), item(1, 100, 120, "c")])
    v1 = next(s for s in shots if s["path"] == "a")
    assert (v1["start"], v1["end"]) == (50, 100)  # el tramo visible más largo del clip tapado
    assert [s["path"] for s in shots] == ["a", "b", "c"]
    assert A.visible_shots([item(1, 0, 10), item(2, 0, 10, "b")])[0]["path"] == "b"  # tapado entero: no es plano


def test_repeated_media_and_markers():
    shots = A.visible_shots([item(1, 0, 50, "a", src=100, markers={10: "Green", 20: "Blue", 30: "Green"}),
                             item(1, 50, 80, "a", src=130),    # mismo fichero, rango fuente solapado → repetido
                             item(1, 80, 100, "a", src=500)],  # mismo fichero, otro rango → plano nuevo
                            marker_color="Green")
    assert shots[0]["markers"] == [10, 30] and shots[1]["dup_of"] == shots[0]["id"] and shots[2]["dup_of"] is None
    assert A.visible_shots([item(1, 0, 50, markers={10: "Green"})])[0]["markers"] == []  # sin respetar marcadores
    # un marcador en la parte del clip que tapa la pista de encima no cuenta
    covered = A.visible_shots([item(1, 0, 100, markers={10: "Green", 80: "Green"}), item(2, 0, 30, "b")], "Green")
    assert next(s for s in covered if s["path"] == "a.mov")["markers"] == [80]


def test_pick_export():
    jobs = [{"TimelineName": "T", "status": "Complete", "RenderMode": "Single clip", "MarkIn": 0, "MarkOut": 99,
             "TargetDir": "/r", "OutputFilename": "old.mov"},
            {"TimelineName": "T", "status": "Complete", "RenderMode": "Single clip", "MarkIn": 0, "MarkOut": 99,
             "TargetDir": "/r", "OutputFilename": "new.mov"},
            {"TimelineName": "T", "status": "Complete", "RenderMode": "Single clip", "MarkIn": 10, "MarkOut": 99,
             "TargetDir": "/r", "OutputFilename": "partial.mov"},
            {"TimelineName": "T", "status": "Failed", "RenderMode": "Single clip", "MarkIn": 0, "MarkOut": 99,
             "TargetDir": "/r", "OutputFilename": "failed.mov"}]
    times = {"/r/old.mov": 1, "/r/new.mov": 2, "/r/partial.mov": 3, "/r/failed.mov": 4}
    assert A.pick_export(jobs, "T", 0, 100, exists=lambda p: True, mtime=times.get) == ("/r/new.mov", 0)
    assert A.pick_export(jobs, "T", 0, 100, exists=lambda p: p != "/r/new.mov", mtime=times.get) == ("/r/old.mov", 0)
    assert A.pick_export(jobs, "Otro", 0, 100, exists=lambda p: True, mtime=times.get) is None


def test_sample_frames():
    f = A.sample_frames(1000, 1100, 12)
    assert len(f) == 12 and f[0] == 1010 and f[-1] == 1089
    assert A.sample_frames(0, 5, 12) == [0, 1, 2, 3, 4]


def test_label_puts_rec_tc_first():
    assert A.still_label("A003C010_260827_R1K0.mov", 90217, 25) == "01:00:08:17 · A003C010_260827_R1K0"


def test_settings_roundtrip(tmp_path):
    p = tmp_path / "s" / "settings.json"
    assert A.load_settings(p) == {}
    A.save_settings({"min": 0, "max": 3, "tracks": [1, 2]}, p)
    assert A.load_settings(p) == {"min": 0, "max": 3, "tracks": [1, 2]}
