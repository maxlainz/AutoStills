# 03 — Primera prueba del owner en Resolve (2026-10-22)

**TL;DR.** La ventana no encontraba el export aunque existía. Había dos fallos de supuesto sobre la API de render (H6, H7). Ahora el fichero se busca en las subcarpetas y el inicio se lee del timecode del propio `.mov`. El botón de ajustes pasa a un «⋯».

## H6 — La API no da la subcarpeta del render
- `RenderJobInfo.TargetDir` da la carpeta de render elegida, pero el fichero estaba en una subcarpeta dentro de ella (`…/_RENDERS/WIP/…`). `os.path.exists(TargetDir/OutputFilename)` era falso.
- Arreglo: `find_file` busca `OutputFilename` bajando hasta dos niveles desde `TargetDir`.

## H7 — `MarkIn`/`MarkOut` del trabajo no son el rango renderizado
- El trabajo decía `MarkIn` 90000 y `MarkOut` 95262 (01:00:00:00–…), pero el fichero empieza en el timecode 00:59:52:00 (frame 89800, el inicio del timeline, leader incluido) y tiene 5463 frames, el timeline entero. Comprobado con `ffprobe -show_entries stream_tags=timecode` y el número de frames.
- Además, exigir que el render cubriera todo el timeline descartaba un render que empieza después del leader.
- Arreglo:
  - `mov_start_frame` lee el timecode del fichero, de la pista `tmcd` del `.mov` y solo en las cabeceras (stdlib, sin ffprobe). Comprobado: 89800 en el render y 413700 (04:35:48:00) en un clip de cámara, que coincide con ffprobe.
  - Si no hay timecode, o es de otro fps, se supone que empieza al inicio del timeline. La comprobación plano a plano (D17) lo confirma o manda los planos al muestreo.
  - Ya no se exige que cubra todo el timeline: los planos que quedan fuera no cuadran y se muestrean.

## H8 — Decodificar el render real
- H.265 10 bits 4:2:0 a 1600×1080: OpenCV lo lee a **2 ms por frame** (300 frames), así que los 5463 frames del timeline se leen en ~11 s.

## Cambios en la ventana
- «Guardar ajustes como predeterminados» queda detrás de un botón «⋯» en la esquina (petición del owner).

## Marcadores al timeline (D23)
- El owner los quiere en el timeline, no en el clip. Se borraron los 54 marcadores de clip que había dejado la v2 (`DeleteMarkerByCustomData("AutoStills")` clip a clip; quedan 0 de clip y 0 de timeline).
- Ahora se escriben con `Timeline.AddMarker(frame − inicio del timeline, …)` y se leen con `Timeline.GetMarkers()`. Supuesto por comprobar a ojo: la clave es el offset desde el inicio del timeline.
- Al leer los marcadores de clip antes de borrarlos, la clave salió igual a la que se escribió (p. ej. 104 en un clip que empieza en 90000 con nombre 01:00:04:04 = 90104). Eso no dice dónde los dibujó Resolve; ya da igual.

## Siguiente paso
- Que el owner relance la prueba: el export ya aparece. Siguen pendientes los supuestos de la bitácora 02: la posición de los marcadores, Grab Still en la Color page y el umbral de la comprobación.
