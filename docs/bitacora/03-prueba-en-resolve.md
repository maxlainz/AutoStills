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

## «No ha hecho algún still que debería» (owner)
Se reprodujo el análisis fuera de Resolve: el render del timeline y los 49 planos leídos por el MCP en solo lectura, con el preset gallery, de 0 a 3 (`scratchpad/diag/run.py`, fuera del repo). Salieron tres problemas:
1. **H9 — El plano largo del final (1253 frames) fallaba con `IndexError` y se quedaba sin still.** `segs[-2] += segs.pop()` en `select.framings`: la lista encoge antes de asignar. Solo pasa con dos tramos y el último corto. Corregido, con test de regresión.
2. **H10 — Un plano se daba por «repetido» cuando no lo era.** Compartía 12 frames de 81 del mismo clip de cámara con otro plano. Ahora es repetido solo si se solapa más de la mitad del rango fuente del más corto.
3. **H11 — Los encuadres se medían mal.** Comparar miniaturas de 16×9 no ve un pull-back en una escena oscura (distancia 0,06 frente al umbral de 0,10), y con contraste normalizado los actores moviéndose parecen encuadres nuevos.
   - Ahora se mide **la cámara**: flujo óptico de puntos con RANSAC (`metrics.camera_step`), escala y desplazamiento acumulados. Hay otro encuadre cuando la cámara se acerca o se aleja un 25 % o se desplaza un cuarto del cuadro; un encuadre tiene que durar ≥ 1 s; los tramos intermedios en los que la cámara está moviéndose se unen al siguiente; los vecinos con la misma posición típica se juntan.
   - Medido: el plano largo hace un pull-back a escala 0,57 en ~4 s y después se queda quieto → **2 encuadres**. El plano del señor de las cartas (escala 1,0, 3 % de desplazamiento) da 1. Coste: ~5 ms por frame.
   - Además, el recorte de bordes del 10 % se limita a 25 frames: en el plano largo eran 5 s y se comía el encuadre cerrado del principio.
- Resultado en el timeline entero: los 49 planos dan still; 55 stills; 6 planos con 2 (cámaras que se mueven, el plano largo incluido); 103 s con el export.

## H12 — Codificación de ficheros
- Al ejecutar la ventana desde el MCP, Python abrió el script como ASCII. Una ruta con acentos rompería el job. Ahora todos los `open()` de texto llevan `encoding="utf-8"` y el worker se lanza con `PYTHONUTF8=1`.

## Ventana
- El owner ve textos que se pisan o desaparecen detrás de otros elementos. Cambios a ciegas, sin captura todavía:
  - etiquetas de ancho fijo para que los controles queden en columna;
  - textos largos con ajuste de línea y altura mínima;
  - la línea del export en su propia fila;
  - ventana de 680×760 como mínimo.
- No se pudo hacer la captura desde el MCP: la ventana no aparece en la pantalla capturada. Hace falta una captura del owner.

## Siguiente paso
- Que el owner relance la prueba: el export ya aparece. Siguen pendientes los supuestos de la bitácora 02: la posición de los marcadores, Grab Still en la Color page y el umbral de la comprobación.
