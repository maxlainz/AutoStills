"""AutoStills — Workspace › Scripts › AutoStills (DaVinci Resolve Studio ≥ 21.1, macOS; D9).

Elige el mejor still de cada plano del timeline y lo guarda en un álbum nuevo de la Gallery (D8).
Este fichero corre con el Python de Resolve: solo stdlib (norma resolve.md). El análisis lo hace el worker
(`autostills/`) en el entorno que crea install.command (D11), lanzado como proceso aparte.
"""
import json
import os
import shutil
import subprocess
import time
from datetime import datetime

__version__ = "0.0.0"
HOME_DIR = os.path.expanduser("~/Library/Application Support/AutoStills")  # lo crea install.command
CACHE_DIR = os.path.expanduser("~/Library/Caches/AutoStills")              # frames temporales; se borran al acabar
PRESETS = [("gallery", "Gallery de referencia"), ("social", "Miniatura / redes"), ("contact", "Contact sheet")]
MARKER_COLORS = ["Green", "Blue", "Cyan", "Yellow", "Red", "Pink", "Purple", "Fuchsia", "Rose", "Lavender", "Sky",
                 "Mint", "Lemon", "Sand", "Cocoa", "Cream"]
SAMPLES_PER_SHOT = 12    # shortcut: fijo hasta medir cuántos hacen falta (H4: ~0,5 s por frame muestreado)
CHECK_THRESHOLD = 0.03   # shortcut: sin calibrar en Resolve; por encima, el plano no cuadra con el export (D17)


# ---------------------------------------------------------------- lógica pura (sin Resolve; tests/test_gui.py)

def tc(frame, fps):
    """Frame absoluto de timeline → timecode non-drop. shortcut: drop frame (29,97 DF) sin soporte."""
    fps = round(float(fps))
    s, fr = divmod(int(frame), fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d:%02d" % (h, m, s, fr)


def _subtract(seg, covers):
    """Tramos de `seg` que no tapa ningún tramo de `covers` (pistas de encima)."""
    out = [seg]
    for c0, c1 in covers:
        out = [p for a, b in out for p in ((a, min(b, c0)), (max(a, c1), b)) if p[1] > p[0]]
    return out


def visible_shots(items, marker_color=None):
    """`items`: clips con media de las pistas elegidas, dicts {track, start, end, name, path, src, uid, markers}.
    La pista de encima tapa a la de abajo (es lo que sale en el render); de cada clip se queda su tramo visible más
    largo. Criterio 19: un clip que repite media ya usada (mismo fichero, rango fuente solapado) no da otro still.
    Criterio 17: un marcador del color elegido dentro del tramo fija el frame."""
    shots = []
    for it in sorted(items, key=lambda i: (i["start"], -i["track"])):
        covers = [(o["start"], o["end"]) for o in items if o["track"] > it["track"]
                  and o["start"] < it["end"] and o["end"] > it["start"]]
        segs = _subtract((it["start"], it["end"]), covers)
        if not segs:
            continue
        a, b = max(segs, key=lambda p: p[1] - p[0])
        src = (it["src"] + a - it["start"], it["src"] + b - it["start"])
        dup = next((s["id"] for s in shots if s["path"] == it["path"] and s["src"][0] < src[1] and src[0] < s["src"][1]),
                   None)
        marker = None
        if marker_color:
            hits = sorted(it["start"] + off for off, color in it["markers"].items()
                          if color == marker_color and a <= it["start"] + off < b)
            marker = hits[0] if hits else None
        shots.append({"id": f"{it['track']}:{it['start']}", "name": it["name"], "path": it["path"], "uid": it.get("uid"),
                      "start": a, "end": b, "src": src, "marker": marker, "dup_of": dup})
    return shots


def pick_export(jobs, tl_name, tl_start, tl_end, exists=os.path.exists, mtime=os.path.getmtime):
    """D17: el último export válido de este timeline en la cola de render → (ruta, frame de timeline del frame 0)."""
    best = None
    for j in jobs:
        path = os.path.join(j.get("TargetDir") or "", j.get("OutputFilename") or "")
        if (j.get("TimelineName") == tl_name and j.get("status") == "Complete" and j.get("RenderMode") == "Single clip"
                and j.get("IsExportVideo", True) and j.get("MarkIn", tl_start) <= tl_start
                and j.get("MarkOut", tl_end) >= tl_end - 1 and j.get("OutputFilename") and exists(path)):
            if best is None or mtime(path) > best[2]:
                best = (path, j.get("MarkIn", tl_start), mtime(path))
    return best[:2] if best else None


def sample_frames(start, end, k=SAMPLES_PER_SHOT):
    """k frames repartidos por el plano, sin el primer y el último 10 % (criterio 5)."""
    a, b = start + (end - start) // 10, end - (end - start) // 10
    if b - a <= k:
        return list(range(a, max(b, a + 1)))
    return sorted({a + round(i * (b - 1 - a) / (k - 1)) for i in range(k)})


def still_label(name, frame, fps):
    return f"{os.path.splitext(name)[0]} · {tc(frame, fps)}"


# ---------------------------------------------------------------- Resolve

def read_items(tl, tracks, only_selected=False):
    sel = {c.GetUniqueId() for c in (tl.GetSelectedClips() or [])} if only_selected else None
    out = []
    for t in tracks:
        for it in tl.GetItemListInTrack("video", t) or []:
            mpi = it.GetMediaPoolItem()
            path = mpi.GetClipProperty("File Path") if mpi else ""
            # criterio 20: títulos, generadores y compuestos sin media no son planos
            if not path or not it.GetClipEnabled() or (sel is not None and it.GetUniqueId() not in sel):
                continue
            # shortcut: se asume que las claves de GetMarkers() son offsets desde el inicio del clip (sin verificar)
            markers = {int(k): (v or {}).get("color") for k, v in (it.GetMarkers() or {}).items()}
            out.append({"track": t, "start": it.GetStart(), "end": it.GetEnd(), "name": it.GetName(), "path": path,
                        "src": it.GetLeftOffset(), "uid": it.GetUniqueId(), "markers": markers})
    return out


def find_export(project, tl):
    jobs = []
    for j in project.GetRenderJobList() or []:
        st = project.GetRenderJobStatus(j.get("JobId")) or {}
        jobs.append({**j, "status": st.get("JobStatus")})
    return pick_export(jobs, tl.GetName(), tl.GetStartFrame(), tl.GetEndFrame())


def gui(resolve, bmd):
    fu = resolve.Fusion()
    ui = fu.UIManager
    disp = bmd.UIDispatcher(ui)
    project = resolve.GetProjectManager().GetCurrentProject()
    tl = project.GetCurrentTimeline() if project else None
    if not tl:
        print("AutoStills: abre un timeline antes de lanzar el script.")
        return
    fps = tl.GetSetting("timelineFrameRate")
    n_tracks = int(tl.GetTrackCount("video") or 1)
    python = os.path.join(HOME_DIR, ".venv", "bin", "python")
    st = {"phase": "idle", "queue": [], "after": None, "proc": None, "export": find_export(project, tl), "log": [],
          "restore": None, "tmp": None}

    track_boxes = [ui.CheckBox({"ID": f"V{t}", "Text": f"V{t}", "Checked": t == 1, "Weight": 0})
                   for t in range(1, n_tracks + 1)]
    win = disp.AddWindow({"ID": "AutoStills", "WindowTitle": f"AutoStills {__version__}", "Geometry": [200, 120, 560, 520]},
        ui.VGroup({"Spacing": 6}, [
            ui.Label({"ID": "Head", "Weight": 0}),
            ui.HGroup({"Weight": 0}, [ui.Label({"Text": "Preset:", "Weight": 0}), ui.ComboBox({"ID": "Preset"})]),
            ui.HGroup({"Weight": 0}, [ui.Label({"Text": "Stills por plano:", "Weight": 0}),
                                      ui.SpinBox({"ID": "N", "Minimum": 1, "Maximum": 5, "Value": 1})]),
            ui.HGroup({"Weight": 0}, [ui.Label({"Text": "Pistas:", "Weight": 0})] + track_boxes),
            ui.HGroup({"Weight": 0}, [ui.Label({"Text": "Planos:", "Weight": 0}), ui.ComboBox({"ID": "Scope"})]),
            ui.HGroup({"Weight": 0}, [ui.Label({"Text": "Fuente:", "Weight": 0}), ui.ComboBox({"ID": "Source"})]),
            ui.HGroup({"Weight": 0}, [ui.Label({"ID": "ExportInfo", "WordWrap": True}),
                                      ui.Button({"ID": "Browse", "Text": "Elegir fichero…", "Weight": 0})]),
            ui.HGroup({"Weight": 0}, [ui.CheckBox({"ID": "UseMarkers", "Text": "Marcadores mandan", "Checked": True}),
                                      ui.ComboBox({"ID": "MarkerColor"})]),
            ui.HGroup({"Weight": 0}, [ui.Label({"Text": "Álbum:", "Weight": 0}), ui.LineEdit({"ID": "Album"})]),
            ui.Label({"ID": "Status", "WordWrap": True, "Weight": 0}),
            ui.TextEdit({"ID": "Summary", "ReadOnly": True, "Weight": 1}),
            ui.HGroup({"Weight": 0}, [ui.HGap(0, 1), ui.Button({"ID": "Cancel", "Text": "Cancelar", "Weight": 0}),
                                      ui.Button({"ID": "Run", "Text": "Sacar stills", "Weight": 0})]),
        ]))
    itm = win.GetItems()
    for _, label in PRESETS:
        itm["Preset"].AddItem(label)
    for label in ("Todo el timeline", "Clips seleccionados"):
        itm["Scope"].AddItem(label)
    for label in ("Último export del timeline (mejor)", "Desde el timeline (muestreo)"):
        itm["Source"].AddItem(label)
    for c in MARKER_COLORS:
        itm["MarkerColor"].AddItem(c)
    itm["Album"].Text = f"AutoStills {datetime.now():%Y-%m-%d %H:%M}"
    itm["Cancel"].Enabled = False

    def say(msg):
        st["log"].append(msg)
        itm["Summary"].PlainText = "\n".join(st["log"])

    def refresh(ev=None):
        tracks = [t for t in range(1, n_tracks + 1) if itm[f"V{t}"].Checked]
        shots = visible_shots(read_items(tl, tracks))
        itm["Head"].Text = f"<b>Timeline:</b> {tl.GetName()} · {len(shots)} planos en " + ", ".join(f"V{t}" for t in tracks)
        exp = st["export"]
        itm["ExportInfo"].Text = (f"Export: {os.path.basename(exp[0])} · "
                                  f"{datetime.fromtimestamp(os.path.getmtime(exp[0])):%d/%m %H:%M}" if exp
                                  else "No hay export válido en la cola de render")

    def browse(ev):
        p = fu.RequestFile(os.path.expanduser("~"))
        if p:
            st["export"] = (str(p), tl.GetStartFrame())  # shortcut: se asume que el fichero empieza al inicio del timeline
            refresh()

    def busy(on):
        itm["Run"].Enabled = not on
        itm["Cancel"].Enabled = on

    def restore():
        if st["restore"]:
            page, timecode = st["restore"]
            tl.SetCurrentTimecode(timecode)
            resolve.OpenPage(page)
            st["restore"] = None
        if st["tmp"]:
            shutil.rmtree(st["tmp"], ignore_errors=True)  # frames del proyecto: nunca se quedan en disco
            st["tmp"] = None

    def worker(job, then):
        if not os.path.exists(python):
            say("✗ Falta el entorno del análisis. Vuelve a lanzar install.command.")
            return finish()
        jp, rp, pp = (os.path.join(st["tmp"], n) for n in ("job.json", "result.json", "progress.txt"))
        with open(jp, "w") as fh:
            json.dump(job, fh)
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}  # que no herede el Python de Resolve
        st["proc"] = subprocess.Popen([python, "-m", "autostills.worker", jp, rp], cwd=os.path.join(HOME_DIR, "app"),
                                      stdout=open(pp, "w"), stderr=open(pp + ".err", "w"), env=env)
        st.update(phase="worker", after=then, files=(rp, pp))

    def export_frames(frames, then):
        st["queue"] = [(f, os.path.join(st["tmp"], f"{f}.jpg")) for f in frames]
        st.update(phase="export", after=then, total=len(st["queue"]))

    def run(ev):
        st["log"] = []
        tracks = [t for t in range(1, n_tracks + 1) if itm[f"V{t}"].Checked]
        color = MARKER_COLORS[itm["MarkerColor"].CurrentIndex] if itm["UseMarkers"].Checked else None
        shots = visible_shots(read_items(tl, tracks, itm["Scope"].CurrentIndex == 1), color)
        st["shots"] = shots
        st["todo"] = [s for s in shots if s["marker"] is None and s["dup_of"] is None]
        st["via"] = {s["id"]: "marcador" for s in shots if s["marker"] is not None}
        st["via"].update({s["id"]: "repetido" for s in shots if s["dup_of"] is not None and s["marker"] is None})
        if not shots:
            return say("No hay planos con media en las pistas elegidas.")
        st["restore"] = (resolve.GetCurrentPage(), tl.GetCurrentTimecode())
        st["tmp"] = os.path.join(CACHE_DIR, f"run_{int(time.time())}")
        os.makedirs(st["tmp"], exist_ok=True)
        busy(True)
        timer.Start()
        use_export = itm["Source"].CurrentIndex == 0 and st["export"]
        if itm["Source"].CurrentIndex == 0 and not st["export"]:
            say("No hay export válido: se analiza por muestreo desde el timeline.")
        if use_export:
            mids = {s["id"]: (s["start"] + s["end"]) // 2 for s in st["todo"]}
            export_frames(sorted(mids.values()), lambda: worker(
                {"source": "check", "video": st["export"][0], "video_first_frame": st["export"][1],
                 "frames": {str(f): os.path.join(st["tmp"], f"{f}.jpg") for f in mids.values()}},
                lambda res: after_check(res, mids)))
        else:
            sample(st["todo"], video=False)

    def after_check(res, mids):
        diff = res.get("diff", {})
        bad = [s for s in st["todo"] if diff.get(str(mids[s["id"]])) is None or diff[str(mids[s["id"]])] > CHECK_THRESHOLD]
        say(f"Comprobación del export: {len(st['todo']) - len(bad)} planos cuadran, {len(bad)} no (se muestrean).")
        sample(bad, video=True)

    def sample(bad, video):
        frames = {s["id"]: sample_frames(s["start"], s["end"]) for s in bad}
        st["via"].update({s["id"]: "muestreo" for s in bad})
        st["via"].update({s["id"]: "export" for s in st["todo"] if s["id"] not in st["via"]})

        def analyse():
            shots = []
            for s in st["todo"]:
                d = {"id": s["id"], "start": s["start"], "end": s["end"]}
                if s["id"] in frames:
                    d["frames"] = {str(f): os.path.join(st["tmp"], f"{f}.jpg") for f in frames[s["id"]]}
                shots.append(d)
            job = {"source": "video" if video else "frames", "shots": shots, "frames": {},
                   "preset": PRESETS[itm["Preset"].CurrentIndex][0], "n": int(itm["N"].Value)}
            if video:
                job.update(video=st["export"][0], video_first_frame=st["export"][1])
            worker(job, grab)
        export_frames(sorted({f for fs in frames.values() for f in fs}), analyse)

    def grab(res):
        picks = [(s["id"], s["marker"]) for s in st["shots"] if s["marker"] is not None]
        flags = {}
        for r in res.get("shots", []):
            picks += [(r["id"], p["frame"]) for p in r["picks"]]
            flags[r["id"]] = r["flags"]
        st["flags"] = flags
        gallery = project.GetGallery()
        album = gallery.CreateGalleryStillAlbum()
        gallery.SetAlbumName(album, itm["Album"].Text)
        gallery.SetCurrentStillAlbum(album)
        resolve.OpenPage("color")  # shortcut: se asume que GrabStill necesita la Color page (sin verificar)
        names = {s["id"]: s["name"] for s in st["shots"]}
        st["queue"] = [(names[i], f) for i, f in sorted(picks, key=lambda p: p[1])]
        st.update(phase="grab", album=album, total=len(st["queue"]), grabbed=0)

    def finish():
        timer.Stop()
        restore()
        busy(False)
        st["phase"] = "idle"
        if st.get("flags") is not None:
            via = st["via"]
            say(f"✓ {st.get('grabbed', 0)} stills en el álbum «{itm['Album'].Text}».")
            for v in ("export", "muestreo", "marcador", "repetido"):
                ids = [i for i, x in via.items() if x == v]
                if ids:
                    say(f"  {v}: {len(ids)} planos")
            for label, key in (("sin cara", "sin_cara"), ("sin frames", "sin_frames"), ("con error", "error")):
                ids = [i for i, f in st["flags"].items() if any(x.startswith(key) for x in f)]
                if ids:
                    say(f"  {label}: {', '.join(ids)}")
            st["flags"] = None
            itm["Album"].Text = f"AutoStills {datetime.now():%Y-%m-%d %H:%M}"

    def tick(ev=None):
        try:
            if st["phase"] == "export":
                if st["queue"]:
                    f, path = st["queue"].pop(0)
                    tl.SetCurrentTimecode(tc(f, fps))
                    project.ExportCurrentFrameAsStill(path)
                    itm["Status"].Text = f"Leyendo frames de Resolve {st['total'] - len(st['queue'])}/{st['total']}"
                else:
                    st["phase"] = "next"
                    st["after"]()
            elif st["phase"] == "worker":
                rp, pp = st["files"]
                try:
                    with open(pp) as fh:
                        last = [x for x in fh.read().splitlines() if x.strip()][-1:]
                    if last:
                        p = json.loads(last[0])
                        itm["Status"].Text = f"Analizando… {int(p['progress'] * 100)} % · plano {p['shot']}"
                except (OSError, ValueError):
                    pass
                code = st["proc"].poll()
                if code is not None:
                    st["proc"] = None
                    if code != 0 or not os.path.exists(rp):
                        with open(pp + ".err") as fh:
                            say("✗ El análisis falló:\n" + fh.read()[-1500:])
                        return finish()
                    with open(rp) as fh:
                        res = json.load(fh)
                    st["phase"] = "next"
                    st["after"](res)
            elif st["phase"] == "grab":
                if st["queue"]:
                    name, f = st["queue"].pop(0)
                    tl.SetCurrentTimecode(tc(f, fps))
                    still = tl.GrabStill()
                    if still:
                        st["album"].SetLabel(still, still_label(name, f, fps))
                        st["grabbed"] += 1
                    itm["Status"].Text = f"Sacando stills {st['total'] - len(st['queue'])}/{st['total']}"
                else:
                    itm["Status"].Text = "Listo."
                    finish()
        except Exception as e:  # que un fallo no deje la ventana colgada ni el cabezal fuera de sitio
            say(f"✗ {type(e).__name__}: {e}")
            finish()

    def cancel(ev=None):
        if st["proc"]:
            st["proc"].terminate()
            st["proc"] = None
        st["queue"] = []
        st["flags"] = None
        say("Cancelado.")
        itm["Status"].Text = ""
        finish()

    def close(ev):
        cancel()
        disp.ExitLoop()

    timer = ui.Timer({"ID": "Tick", "Interval": 20})
    win.On.AutoStills.Close = close
    win.On.Run.Clicked = run
    win.On.Cancel.Clicked = cancel
    win.On.Browse.Clicked = browse
    for t in range(1, n_tracks + 1):
        win.On[f"V{t}"].Clicked = refresh
    # según la versión el temporizador llega como disp.On.Timeout o disp.On.<ID>.Timeout (hallazgo de MHL MediaManagement)
    disp.On.Timeout = tick
    try:
        disp.On.Tick.Timeout = tick
    except Exception:
        pass
    refresh()
    win.Show()
    disp.RunLoop()
    win.Hide()


if "resolve" in globals() and "bmd" in globals():  # lanzado desde Workspace › Scripts (__name__ no es "__main__")
    gui(resolve, bmd)  # noqa: F821
