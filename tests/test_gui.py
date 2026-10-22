"""Lógica pura de la ventana (AutoStills.py), sin Resolve."""
import AutoStills as A


def item(track, start, end, path="a.mov", src=0, name="clip.mov"):
    return {"track": track, "start": start, "end": end, "path": path, "src": src, "name": name, "uid": f"{track}-{start}"}


def test_tc():
    assert A.tc(90000, 25) == "01:00:00:00" and A.tc(90217, 25.0) == "01:00:08:17" and A.tc(86400 + 23, 23.976) == "01:00:00:23"


def test_upper_track_covers_lower():
    shots = A.visible_shots([item(1, 0, 100, "a"), item(2, 30, 50, "b"), item(1, 100, 120, "c")])
    v1 = next(s for s in shots if s["path"] == "a")
    assert (v1["start"], v1["end"]) == (50, 100)  # el tramo visible más largo del clip tapado
    assert [s["path"] for s in shots] == ["a", "b", "c"]
    assert A.visible_shots([item(1, 0, 10), item(2, 0, 10, "b")])[0]["path"] == "b"  # tapado entero: no es plano


def test_repeated_media_and_markers():
    # el caso real de la bitácora 03: mismo clip, 12 frames compartidos de 81 → no es repetido
    real = A.visible_shots([item(1, 0, 31, "c", src=1610), item(1, 100, 181, "c", src=1541)])
    assert real[1]["dup_of"] is None
    tlm = {10: "Green", 20: "Blue", 30: "Green", 60: "Green"}  # marcadores del timeline (D23), frames absolutos
    shots = A.visible_shots([item(1, 0, 50, "a", src=100),
                             item(1, 50, 80, "a", src=130),    # mismo fichero, rango fuente solapado → repetido
                             item(1, 80, 100, "a", src=500)],  # mismo fichero, otro rango → plano nuevo
                            "Green", tlm)
    assert shots[0]["markers"] == [10, 30] and shots[1]["markers"] == [60]
    assert shots[1]["dup_of"] == shots[0]["id"] and shots[2]["dup_of"] is None
    assert A.visible_shots([item(1, 0, 50)], None, tlm)[0]["markers"] == []  # sin respetar marcadores
    # un marcador en la parte del clip que tapa la pista de encima es del plano de encima
    covered = A.visible_shots([item(1, 0, 100), item(2, 0, 30, "b")], "Green", {10: "Green", 80: "Green"})
    assert {s["path"]: s["markers"] for s in covered} == {"a.mov": [80], "b": [10]}


def test_pick_export():
    def job(name, status="Complete", mode="Single clip", tl="T"):
        return {"TimelineName": tl, "status": status, "RenderMode": mode, "TargetDir": "/r", "OutputFilename": name,
                "MarkIn": 90000}  # MarkIn no es el rango renderizado (bitácora 03): no se usa
    jobs = [job("old.mov"), job("new.mov"), job("failed.mov", status="Failed"), job("clips.mov", mode="Individual clips")]
    times = {"/r/sub/old.mov": 1, "/r/sub/new.mov": 2, "/r/sub/failed.mov": 3, "/r/sub/clips.mov": 4}
    locate = lambda d, n: f"{d}/sub/{n}"  # noqa: E731 — el fichero está en una subcarpeta que la API no da
    assert A.pick_export(jobs, "T", 89800, 25, locate, times.get, lambda p: (89800, 25)) == ("/r/sub/new.mov", 89800)
    assert A.pick_export(jobs, "T", 89800, 25, locate, times.get, lambda p: None) == ("/r/sub/new.mov", 89800)
    assert A.pick_export(jobs, "T", 89800, 25, locate, times.get, lambda p: (90000, 24))[1] == 89800  # otro fps
    assert A.pick_export(jobs, "T", 0, 25, lambda d, n: None, times.get) is None
    assert A.pick_export(jobs, "Otro", 0, 25, locate, times.get) is None


def _atom(typ, body):
    return (8 + len(body)).to_bytes(4, "big") + typ + body


def test_mov_start_frame(tmp_path):
    # .mov mínimo con una pista tmcd: el primer sample (en mdat) es el número de frame del timecode
    entry = b"tmcd" + bytes(6) + (1).to_bytes(2, "big") + bytes(4) + bytes(4) + (25000).to_bytes(4, "big") \
        + (1000).to_bytes(4, "big") + bytes([25]) + bytes(3)
    stsd = _atom(b"stsd", bytes(4) + (1).to_bytes(4, "big") + (4 + len(entry)).to_bytes(4, "big") + entry)
    mdat = _atom(b"mdat", (89800).to_bytes(4, "big"))
    def build(offset):
        stco = _atom(b"stco", bytes(4) + (1).to_bytes(4, "big") + offset.to_bytes(4, "big"))
        trak = _atom(b"trak", _atom(b"mdia", _atom(b"minf", _atom(b"stbl", stsd + stco))))
        return _atom(b"ftyp", b"qt  ") + _atom(b"moov", trak)
    head = build(0)
    data = build(len(head) + 8) + mdat
    p = tmp_path / "t.mov"
    p.write_bytes(data)
    assert A.mov_start_frame(str(p)) == (89800, 25)
    (tmp_path / "x.mov").write_bytes(b"no es un mov")
    assert A.mov_start_frame(str(tmp_path / "x.mov")) is None


def test_find_file(tmp_path):
    (tmp_path / "WIP").mkdir()
    (tmp_path / "WIP" / "a.mov").write_bytes(b"")
    assert A.find_file(str(tmp_path), "a.mov") == str(tmp_path / "WIP" / "a.mov")
    assert A.find_file(str(tmp_path), "b.mov") is None and A.find_file("", "a.mov") is None


def test_sample_frames():
    f = A.sample_frames(1000, 1100, 12)
    assert len(f) == 12 and f[0] == 1010 and f[-1] == 1089
    assert A.sample_frames(0, 5, 12) == [0, 1, 2, 3, 4]


def test_label_sorts_by_frame_then_tc():
    assert A.still_label("A003C010_260827_R1K0.mov", 90217, 25) == "0090217 · 01:00:08:17 · A003C010_260827_R1K0"
    labels = [A.still_label("c.mov", f, 25) for f in (95262, 90217, 100000)]
    assert sorted(labels) == [labels[1], labels[0], labels[2]]  # orden alfabético = orden de la peli


def test_settings_roundtrip(tmp_path):
    p = tmp_path / "s" / "settings.json"
    assert A.load_settings(p) == {}
    A.save_settings({"min": 0, "max": 3, "tracks": [1, 2]}, p)
    assert A.load_settings(p) == {"min": 0, "max": 3, "tracks": [1, 2]}


def test_elide():
    name = "BarraDunBar_BarraDunBar-WIP_rec709_ST20_h265_10b_1600x1080_20261022.mov"
    out = A.elide(name)
    assert len(out) <= 44 and out.startswith("BarraDunBar_") and out.endswith("20261022.mov")
    assert A.elide("corto.mov") == "corto.mov"
