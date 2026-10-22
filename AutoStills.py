"""AutoStills — Workspace › Scripts › AutoStills (DaVinci Resolve Studio ≥ 21.1, macOS; D9).

Elige el mejor still de cada plano del timeline y lo guarda en un álbum nuevo de la Gallery (D8).
Este fichero corre con el Python de Resolve: solo stdlib (norma resolve.md). El análisis lo hace el worker
(`autostills/`) en el entorno que crea install.command (D11), lanzado como proceso aparte.
"""
import json
import os
import shutil
import struct
import subprocess
import time
from datetime import datetime

__version__ = "0.0.0"
HOME_DIR = os.path.expanduser("~/Library/Application Support/AutoStills")  # lo crea install.command
CACHE_DIR = os.path.expanduser("~/Library/Caches/AutoStills")              # frames temporales; se borran al acabar
PRESETS = [("gallery", "Gallery de referencia"), ("social", "Miniatura / redes"), ("contact", "Contact sheet")]
MARKER_COLORS = ["Green", "Blue", "Cyan", "Yellow", "Red", "Pink", "Purple", "Fuchsia", "Rose", "Lavender", "Sky",
                 "Mint", "Lemon", "Sand", "Cocoa", "Cream"]
SETTINGS = os.path.join(HOME_DIR, "settings.json")                       # «Guardar como predeterminado»
MARKER_TAG = "AutoStills"  # customData de los marcadores que deja AutoStills (D20)
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


def visible_shots(items, marker_color=None, tl_markers=None):
    """`items`: clips con media de las pistas elegidas, dicts {track, start, end, name, path, src, uid}.
    `tl_markers`: marcadores del timeline {frame absoluto: color} (D23: van en el timeline, no en el clip).
    La pista de encima tapa a la de abajo (es lo que sale en el render); de cada clip se queda su tramo visible más
    largo. Criterio 19: un clip que repite media ya usada (mismo fichero, más de la mitad del rango fuente solapado)
    no da otro still.
    Criterio 17 / D20: los marcadores del color elegido dentro del tramo son los stills del plano (no se analiza)."""
    shots = []
    for it in sorted(items, key=lambda i: (i["start"], -i["track"])):
        covers = [(o["start"], o["end"]) for o in items if o["track"] > it["track"]
                  and o["start"] < it["end"] and o["end"] > it["start"]]
        segs = _subtract((it["start"], it["end"]), covers)
        if not segs:
            continue
        a, b = max(segs, key=lambda p: p[1] - p[0])
        src = (it["src"] + a - it["start"], it["src"] + b - it["start"])
        # repetido = la mayor parte del material ya está en otro plano; compartir unos frames del mismo clip no basta
        dup = next((s["id"] for s in shots if s["path"] == it["path"]
                    and min(s["src"][1], src[1]) - max(s["src"][0], src[0]) > 0.5 * min(src[1] - src[0], s["src"][1] - s["src"][0])),
                   None)
        marks = sorted(f for f, color in (tl_markers or {}).items() if marker_color and color == marker_color and a <= f < b)
        shots.append({"id": f"{it['track']}:{it['start']}", "name": it["name"], "path": it["path"], "uid": it.get("uid"),
                      "start": a, "end": b, "src": src, "markers": marks, "dup_of": dup})
    return shots


def find_file(target_dir, name, depth=2):
    """La API da la carpeta de render sin la subcarpeta que Resolve puede añadir (bitácora 03): se busca dentro."""
    if not target_dir or not name:
        return None
    for root, dirs, files in os.walk(target_dir):
        if name in files:
            return os.path.join(root, name)
        if root[len(target_dir):].count(os.sep) >= depth - 1:
            dirs[:] = []
    return None


def mov_start_frame(path):
    """Primer frame del timecode de un .mov (pista tmcd) → (frame, fps) o None. Solo lee cabeceras de átomos.
    El MarkIn del trabajo de render no es el rango renderizado (bitácora 03); el timecode del fichero sí."""
    try:
        with open(path, "rb") as fh:
            def atoms(a, b):
                while a + 8 <= b:
                    fh.seek(a)
                    size, typ = struct.unpack(">I4s", fh.read(8))
                    hdr = 8
                    if size == 1:
                        size, hdr = struct.unpack(">Q", fh.read(8))[0], 16
                    elif size == 0:
                        size = b - a
                    if size < hdr:
                        return
                    yield typ, a + hdr, a + size
                    a += size

            def find(a, b, names):
                for typ, x, y in atoms(a, b):
                    if typ == names[0]:
                        yield from ([(x, y)] if len(names) == 1 else find(x, y, names[1:]))

            for moov in find(0, os.fstat(fh.fileno()).st_size, [b"moov"]):
                for trak in find(*moov, [b"trak"]):
                    stbl = next(find(*trak, [b"mdia", b"minf", b"stbl"]), None)
                    stsd = stbl and next(find(*stbl, [b"stsd"]), None)
                    if not stsd:
                        continue
                    fh.seek(stsd[0] + 12)
                    if fh.read(4) != b"tmcd":
                        continue
                    fh.seek(stsd[0] + 12 + 4 + 16 + 8)  # reservado, índice, flags → timescale, frameDuration, nFrames
                    fps = fh.read(1)[0]
                    stco = next(find(*stbl, [b"stco"]), None)
                    co64 = None if stco else next(find(*stbl, [b"co64"]), None)
                    if not (stco or co64):
                        continue
                    fh.seek((stco or co64)[0] + 8)  # versión y flags, número de entradas → primer offset
                    off = struct.unpack(">I", fh.read(4))[0] if stco else struct.unpack(">Q", fh.read(8))[0]
                    fh.seek(off)
                    return struct.unpack(">I", fh.read(4))[0], fps
    except (OSError, struct.error, TypeError, IndexError):
        return None
    return None


def pick_export(jobs, tl_name, tl_start, fps, locate=find_file, mtime=os.path.getmtime, start=mov_start_frame):
    """D17: el último export de este timeline en la cola de render → (ruta, frame de timeline del frame 0 del fichero).
    No hace falta que cubra todo el timeline: los planos que caigan fuera no cuadran en la comprobación y se muestrean."""
    best = None
    for j in jobs:
        if not (j.get("TimelineName") == tl_name and j.get("status") == "Complete"
                and j.get("RenderMode") == "Single clip" and j.get("IsExportVideo", True)):
            continue
        path = locate(j.get("TargetDir"), j.get("OutputFilename"))
        if path and (best is None or mtime(path) > best[2]):
            tcf = start(path)
            # sin timecode legible se supone que empieza al inicio del timeline; la comprobación lo confirma o no
            first = tcf[0] if tcf and tcf[1] == round(float(fps)) else tl_start
            best = (path, first, mtime(path))
    return best[:2] if best else None


def sample_frames(start, end, k=SAMPLES_PER_SHOT):
    """k frames repartidos por el plano, sin el primer y el último 10 % (máx. 25 frames, criterio 5)."""
    edge = min((end - start) // 10, 25)
    a, b = start + edge, end - edge
    if b - a <= k:
        return list(range(a, max(b, a + 1)))
    return sorted({a + round(i * (b - 1 - a) / (k - 1)) for i in range(k)})


def still_label(name, frame, fps):
    """REC TC primero: los stills y los marcadores se ordenan en el orden de la peli, no por nombre de clip (D21)."""
    return f"{tc(frame, fps)} · {os.path.splitext(name)[0]}"


def load_settings(path=SETTINGS):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_settings(values, path=SETTINGS):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(values, fh, indent=1)




# ---------------------------------------------------------------- Resolve

def read_items(tl, tracks, only_selected=False):
    """Clips con media de las pistas elegidas → (dicts para visible_shots, {uid: TimelineItem})."""
    sel = {c.GetUniqueId() for c in (tl.GetSelectedClips() or [])} if only_selected else None
    out, objs = [], {}
    for t in tracks:
        for it in tl.GetItemListInTrack("video", t) or []:
            mpi = it.GetMediaPoolItem()
            path = mpi.GetClipProperty("File Path") if mpi else ""
            # criterio 20: títulos, generadores y compuestos sin media no son planos
            if not path or not it.GetClipEnabled() or (sel is not None and it.GetUniqueId() not in sel):
                continue
            uid = it.GetUniqueId()
            objs[uid] = it
            out.append({"track": t, "start": it.GetStart(), "end": it.GetEnd(), "name": it.GetName(), "path": path,
                        "src": it.GetLeftOffset(), "uid": uid})
    return out, objs


def read_tl_markers(tl):
    """Marcadores del timeline → {frame absoluto: color}. shortcut: claves = offset desde el inicio del timeline
    (convención de la API; comprobar a ojo en la primera prueba)."""
    start = tl.GetStartFrame()
    return {start + int(k): (v or {}).get("color") for k, v in (tl.GetMarkers() or {}).items()}


def find_export(project, tl):
    jobs = []
    for j in project.GetRenderJobList() or []:
        st = project.GetRenderJobStatus(j.get("JobId")) or {}
        jobs.append({**j, "status": st.get("JobStatus")})
    return pick_export(jobs, tl.GetName(), tl.GetStartFrame(), tl.GetSetting("timelineFrameRate"))


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
    cfg = load_settings()
    st = {"phase": "idle", "queue": [], "after": None, "proc": None, "export": find_export(project, tl), "log": [],
          "restore": None, "tmp": None, "steps": [], "result": None}

    def section(text):
        return ui.Label({"Text": f"<b>{text}</b>", "Weight": 0})

    track_boxes = [ui.CheckBox({"ID": f"V{t}", "Text": f"V{t}", "Weight": 0, "MinimumSize": [56, 0],
                                "Checked": t in cfg.get("tracks", [1])}) for t in range(1, n_tracks + 1)]
    LW = 130  # ancho fijo de las etiquetas de la izquierda: los controles quedan en columna y no se pisan

    def row(label, *widgets):
        return ui.HGroup({"Weight": 0, "Spacing": 8},
                         [ui.Label({"Text": label, "Weight": 0, "MinimumSize": [LW, 22], "MaximumSize": [LW, 22]})]
                         + list(widgets))

    win = disp.AddWindow({"ID": "AutoStills", "WindowTitle": f"AutoStills {__version__}",
                          "Geometry": [200, 100, 680, 760], "MinimumSize": [620, 700]},
        ui.VGroup({"Spacing": 8}, [
            ui.HGroup({"Weight": 0}, [section("1 · Qué planos"), ui.HGap(0, 1),
                                      ui.Button({"ID": "More", "Text": "⋯", "Weight": 0, "Flat": True,
                                                 "MinimumSize": [32, 22], "ToolTip": "Más opciones"})]),
            ui.HGroup({"ID": "MoreRow", "Weight": 0, "Hidden": True}, [  # UIManager no tiene menús: fila plegable
                ui.HGap(0, 1), ui.Button({"ID": "Save", "Text": "Guardar ajustes como predeterminados", "Weight": 0})]),
            ui.Label({"ID": "Head", "Weight": 0, "WordWrap": True, "MinimumSize": [0, 36]}),
            row("Pistas", *track_boxes, ui.HGap(0, 1)),
            row("Planos", ui.ComboBox({"ID": "Scope", "MinimumSize": [240, 0]}), ui.HGap(0, 1)),
            ui.VGap(6),
            section("2 · Cómo elegir"),
            row("Preset", ui.ComboBox({"ID": "Preset", "MinimumSize": [240, 0]}), ui.HGap(0, 1)),
            row("Stills por plano", ui.Label({"Text": "de", "Weight": 0}),
                ui.SpinBox({"ID": "Min", "Minimum": 0, "Maximum": 5, "Value": cfg.get("min", 0), "MinimumSize": [60, 0]}),
                ui.Label({"Text": "a", "Weight": 0}),
                ui.SpinBox({"ID": "Max", "Minimum": 1, "Maximum": 5, "Value": cfg.get("max", 3), "MinimumSize": [60, 0]}),
                ui.HGap(0, 1)),
            row("Fuente", ui.ComboBox({"ID": "Source", "MinimumSize": [300, 0]}), ui.HGap(0, 1)),
            row("", ui.Label({"ID": "ExportInfo", "WordWrap": True, "Weight": 1, "MinimumSize": [0, 36]}),
                ui.Button({"ID": "Browse", "Text": "Elegir fichero…", "Weight": 0})),
            row("Marcadores", ui.CheckBox({"ID": "Respect", "Text": "Respetar los existentes de color", "Weight": 0,
                                           "Checked": cfg.get("respect", True)}),
                ui.ComboBox({"ID": "Color", "MinimumSize": [120, 0]}), ui.HGap(0, 1)),
            ui.VGap(6),
            section("3 · Qué hacer con los elegidos"),
            row("", ui.CheckBox({"ID": "OutMarkers", "Checked": cfg.get("out_markers", True), "Weight": 1})),
            row("", ui.CheckBox({"ID": "OutGallery", "Text": "Añadir a la Gallery, en el álbum:", "Weight": 0,
                                 "Checked": cfg.get("out_gallery", False)}),
                ui.LineEdit({"ID": "Album", "Weight": 1})),
            ui.VGap(6),
            ui.Label({"ID": "Status", "WordWrap": True, "Weight": 0, "MinimumSize": [0, 36]}),
            ui.TextEdit({"ID": "Summary", "ReadOnly": True, "Weight": 1, "MinimumSize": [0, 120]}),
            ui.HGroup({"Weight": 0}, [ui.HGap(0, 1), ui.Button({"ID": "Cancel", "Text": "Cancelar", "Weight": 0}),
                                      ui.Button({"ID": "Run", "Text": "Analizar", "Weight": 0, "Default": True,
                                                 "MinimumSize": [110, 0]})]),
        ]))
    itm = win.GetItems()
    for _, label in PRESETS:
        itm["Preset"].AddItem(label)
    for label in ("Todo el timeline", "Clips seleccionados"):
        itm["Scope"].AddItem(label)
    for label in ("Último export del timeline (mejor)", "Desde el timeline (muestreo)"):
        itm["Source"].AddItem(label)
    for c in MARKER_COLORS:
        itm["Color"].AddItem(c)
    for key in ("Preset", "Scope", "Source", "Color"):
        itm[key].CurrentIndex = cfg.get(key.lower(), 0)
    itm["Album"].Text = f"AutoStills {datetime.now():%Y-%m-%d %H:%M}"
    itm["Cancel"].Enabled = False

    def color():
        return MARKER_COLORS[itm["Color"].CurrentIndex]

    def tracks():
        return [t for t in range(1, n_tracks + 1) if itm[f"V{t}"].Checked]

    def say(msg):
        st["log"].append(msg)
        itm["Summary"].PlainText = "\n".join(st["log"])

    def refresh(ev=None):
        shots = visible_shots(read_items(tl, tracks())[0], color(), read_tl_markers(tl))
        marked = sum(1 for s in shots if s["markers"])
        itm["Head"].Text = (f"Timeline: {tl.GetName()} · {len(shots)} planos en " + ", ".join(f"V{t}" for t in tracks())
                            + (f" · {marked} ya con marcadores {color()}" if marked else ""))
        exp = st["export"]
        itm["ExportInfo"].Text = (f"Export: {os.path.basename(exp[0])} · "
                                  f"{datetime.fromtimestamp(os.path.getmtime(exp[0])):%d/%m %H:%M} ✓" if exp
                                  else "No hay export válido en la cola de render")
        itm["OutMarkers"].Text = f"Marcar en el timeline (marcadores {color()})"

    def save(ev):
        save_settings({"tracks": tracks(), "scope": itm["Scope"].CurrentIndex, "preset": itm["Preset"].CurrentIndex,
                       "min": int(itm["Min"].Value), "max": int(itm["Max"].Value), "source": itm["Source"].CurrentIndex,
                       "respect": itm["Respect"].Checked, "color": itm["Color"].CurrentIndex,
                       "out_markers": itm["OutMarkers"].Checked, "out_gallery": itm["OutGallery"].Checked})
        itm["Status"].Text = "Ajustes guardados como predeterminados."
        itm["MoreRow"].Hidden = True

    def more(ev):
        itm["MoreRow"].Hidden = not itm["MoreRow"].Hidden

    def browse(ev):
        p = fu.RequestFile(os.path.expanduser("~"))
        if p:
            tcf = mov_start_frame(str(p))
            st["export"] = (str(p), tcf[0] if tcf and tcf[1] == round(float(fps)) else tl.GetStartFrame())
            refresh()

    def busy(on):
        itm["Run"].Enabled = not on
        itm["Cancel"].Enabled = on

    def step(name, detail=""):
        k = st["steps"].index(name) + 1 if name in st["steps"] else len(st["steps"])
        itm["Status"].Text = f"Paso {k} de {len(st['steps'])} · {name}" + (f" · {detail}" if detail else "")

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
        with open(jp, "w", encoding="utf-8") as fh:
            json.dump(job, fh)
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}  # que no herede el Python de Resolve
        env["PYTHONUTF8"] = "1"  # rutas con acentos aunque Resolve lance el proceso sin locale (bitácora 03)
        st["proc"] = subprocess.Popen([python, "-m", "autostills.worker", jp, rp], cwd=os.path.join(HOME_DIR, "app"),
                                      stdout=open(pp, "w", encoding="utf-8"),
                                      stderr=open(pp + ".err", "w", encoding="utf-8"), env=env)
        st.update(phase="worker", after=then, files=(rp, pp))

    def export_frames(frames, then, label):
        st["queue"] = [(f, os.path.join(st["tmp"], f"{f}.jpg")) for f in frames]
        st.update(phase="export", after=then, total=len(st["queue"]), label=label)

    def run(ev):
        st["log"] = []
        respect = itm["Respect"].Checked
        items, st["objs"] = read_items(tl, tracks(), itm["Scope"].CurrentIndex == 1)
        shots = visible_shots(items, color() if respect else None, read_tl_markers(tl))
        if not shots:
            return say("No hay planos con media en las pistas elegidas.")
        if not (itm["OutMarkers"].Checked or itm["OutGallery"].Checked):
            return say("Elige al menos una salida en el paso 3.")
        st["shots"] = shots
        st["todo"] = [s for s in shots if not s["markers"] and s["dup_of"] is None]
        st["via"] = {s["id"]: "marcadores" for s in shots if s["markers"]}
        st["via"].update({s["id"]: "repetido" for s in shots if s["dup_of"] is not None and not s["markers"]})
        use_export = itm["Source"].CurrentIndex == 0 and st["export"]
        st["steps"] = (["Comprobar el export"] if use_export and st["todo"] else []) + \
                      (["Analizar"] if st["todo"] else []) + ["Marcar y añadir", "Listo"]
        st["restore"] = (resolve.GetCurrentPage(), tl.GetCurrentTimecode())
        st["tmp"] = os.path.join(CACHE_DIR, f"run_{int(time.time())}")
        os.makedirs(st["tmp"], exist_ok=True)
        busy(True)
        timer.Start()
        if itm["Source"].CurrentIndex == 0 and not st["export"]:
            say("No hay export válido: se analiza por muestreo desde el timeline.")
        if not st["todo"]:
            output({"shots": []})
        elif use_export:
            mids = {s["id"]: (s["start"] + s["end"]) // 2 for s in st["todo"]}
            export_frames(sorted(mids.values()), lambda: worker(
                {"source": "check", "video": st["export"][0], "video_first_frame": st["export"][1],
                 "frames": {str(f): os.path.join(st["tmp"], f"{f}.jpg") for f in mids.values()}},
                lambda res: after_check(res, mids)), "Comprobar el export")
        else:
            sample(st["todo"], video=False)

    def after_check(res, mids):
        diff = res.get("diff", {})
        bad = [s for s in st["todo"] if diff.get(str(mids[s["id"]])) is None or diff[str(mids[s["id"]])] > CHECK_THRESHOLD]
        say(f"Export: {len(st['todo']) - len(bad)} planos cuadran con el timeline, {len(bad)} no (se muestrean).")
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
                   "preset": PRESETS[itm["Preset"].CurrentIndex][0], "min": int(itm["Min"].Value),
                   "max": max(int(itm["Max"].Value), int(itm["Min"].Value))}
            if video:
                job.update(video=st["export"][0], video_first_frame=st["export"][1])
            step("Analizar")
            worker(job, output)
        export_frames(sorted({f for fs in frames.values() for f in fs}), analyse, "Analizar")

    def output(res):
        by_id = {s["id"]: s for s in st["shots"]}
        st["result"] = res
        new = []  # (shot, frame, nota) elegidos ahora; los planos con marcadores ya tienen los suyos
        for r in res.get("shots", []):
            new += [(by_id[r["id"]], p["frame"], f"{MARKER_TAG} · {PRESETS[itm['Preset'].CurrentIndex][1]} · "
                     f"{p['score']:.2f}") for p in r["picks"]]
        marked = 0
        if itm["OutMarkers"].Checked:
            for s, f, note in new:
                # D23: en el timeline, no en el clip; frameId = offset desde el inicio del timeline
                if tl.AddMarker(f - tl.GetStartFrame(), color(), still_label(s["name"], f, fps), note, 1, MARKER_TAG):
                    marked += 1
        st["marked"] = marked
        grabs = sorted([(s, f) for s, f, _ in new] + [(s, f) for s in st["shots"] for f in s["markers"]],
                       key=lambda x: x[1])
        if itm["OutGallery"].Checked and grabs:
            gallery = project.GetGallery()
            album = gallery.CreateGalleryStillAlbum()
            gallery.SetAlbumName(album, itm["Album"].Text)
            gallery.SetCurrentStillAlbum(album)
            resolve.OpenPage("color")  # shortcut: se asume que GrabStill necesita la Color page (sin verificar)
            st["queue"] = grabs
            st.update(phase="grab", album=album, total=len(grabs), grabbed=0)
        else:
            st["grabbed"] = 0
            finish()

    def finish():
        timer.Stop()
        restore()
        busy(False)
        st["phase"] = "idle"
        res = st.pop("result", None)
        if res is not None:
            itm["Status"].Text = f"Paso {len(st['steps'])} de {len(st['steps'])} · Listo"
            out = []
            if itm["OutMarkers"].Checked:
                out.append(f"{st['marked']} marcadores {color()} nuevos")
            if itm["OutGallery"].Checked:
                out.append(f"{st['grabbed']} stills en «{itm['Album'].Text}»")
            say("✓ " + " · ".join(out))
            via, flags = st["via"], {r["id"]: r["flags"] for r in res.get("shots", [])}
            names = {s["id"]: s["name"] for s in st["shots"]}
            for v, text in (("export", "analizados con el export"), ("muestreo", "analizados por muestreo"),
                            ("marcadores", "respetados (ya tenían marcadores)"), ("repetido", "repetidos (sin still)")):
                n = sum(1 for x in via.values() if x == v)
                if n:
                    say(f"  {n} planos {text}")
            for key, text in (("descartado", "sin still (cortos o blandos)"), ("sin_cara", "sin cara"),
                              ("error", "con error")):
                ids = [names[i] for i, f in flags.items() if any(x.startswith(key) for x in f)]
                if ids:
                    say(f"  {len(ids)} {text}: " + ", ".join(os.path.splitext(n)[0] for n in ids))
            itm["Album"].Text = f"AutoStills {datetime.now():%Y-%m-%d %H:%M}"
            refresh()

    def tick(ev=None):
        try:
            if st["phase"] == "export":
                if st["queue"]:
                    f, path = st["queue"].pop(0)
                    tl.SetCurrentTimecode(tc(f, fps))
                    project.ExportCurrentFrameAsStill(path)
                    step(st["label"], f"leyendo frames de Resolve {st['total'] - len(st['queue'])}/{st['total']}")
                else:
                    st["phase"] = "next"
                    st["after"]()
            elif st["phase"] == "worker":
                rp, pp = st["files"]
                try:
                    with open(pp, encoding="utf-8") as fh:
                        last = [x for x in fh.read().splitlines() if x.strip()][-1:]
                    if last:
                        p = json.loads(last[0])
                        step(st["steps"][0] if "diff" in last[0] else "Analizar", f"{int(p['progress'] * 100)} %")
                except (OSError, ValueError, KeyError):
                    pass
                code = st["proc"].poll()
                if code is not None:
                    st["proc"] = None
                    if code != 0 or not os.path.exists(rp):
                        with open(pp + ".err", encoding="utf-8") as fh:
                            say("✗ El análisis falló:\n" + fh.read()[-1500:])
                        return finish()
                    with open(rp, encoding="utf-8") as fh:
                        res = json.load(fh)
                    st["phase"] = "next"
                    st["after"](res)
            elif st["phase"] == "grab":
                if st["queue"]:
                    s, f = st["queue"].pop(0)
                    tl.SetCurrentTimecode(tc(f, fps))
                    still = tl.GrabStill()
                    if still:
                        st["album"].SetLabel(still, still_label(s["name"], f, fps))
                        st["grabbed"] += 1
                    step("Marcar y añadir", f"Gallery {st['total'] - len(st['queue'])}/{st['total']}")
                else:
                    finish()
        except Exception as e:  # que un fallo no deje la ventana colgada ni el cabezal fuera de sitio
            say(f"✗ {type(e).__name__}: {e}")
            finish()

    def cancel(ev=None):
        if st["proc"]:
            st["proc"].terminate()
            st["proc"] = None
        st["queue"] = []
        st.pop("result", None)
        if st["phase"] != "idle":
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
    win.On.Save.Clicked = save
    win.On.More.Clicked = more
    win.On.Color.CurrentIndexChanged = refresh
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
