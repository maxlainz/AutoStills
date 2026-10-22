# 01 — Medida: cómo sacar los frames de Resolve (2026-10-22)

**TL;DR.** Primera tanda: la miniatura de la Color page no sirve: es fija por clip y de 576×324 (H1). `Project.ExportCurrentFrameAsStill` sí: exporta el frame del cabezal **graduado y a resolución de timeline**, desde la Edit page, sin tocar el proyecto ni la Gallery. Tarda ~0,5 s por frame dentro de un plano y no da frames atrasados (H2). Decisión: D13. Segunda tanda: el frame exportado es exactamente el del cabezal (H3), y el coste de ~0,5 s está en mover el cabezal, no en exportar, y no se puede esquivar cambiando el orden (H4).

Medido en un proyecto real del owner (Resolve Studio 21.1.0.17, timeline de 1600×1080 a 25 fps, 50 clips en V1, ProRes 4444 a 2048×1152) con el MCP de Resolve (`run_script`). Solo lectura: se movió el cabezal y, en las pruebas de la miniatura, se cambió a la Color page; al final de cada prueba se restauraron la página y el cabezal. Los frames de prueba se escribieron en una carpeta temporal fuera del repo y se borraron.

## Predicción (escrita antes de medir)
- Miniatura: 50–200 ms por frame, ~320 px de ancho, sin saber si cambia con el frame.
- Criterio de viabilidad: ≤ 100 ms/frame y resolución suficiente para caras.

## H1 — La miniatura de la Color page es fija por clip y pequeña
- `Timeline.GetCurrentClipThumbnailImage()`: 576×324, RGB de 8 bits. Devuelve `{}` justo después de `OpenPage("color")`; a los ~0,5 s ya responde.
- Se movió el cabezal 7 veces dentro de un clip (cada 12 frames) y se esperó hasta 1,5 s cada vez: **el hash no cambia**. Cambia entre clips. Es la miniatura del clip, no el frame actual.
- Aunque cambiara, 576×324 no basta: no todo son primeros planos (owner).
- **Predicción fallida**: no vale para analizar frames.

## H2 — `ExportCurrentFrameAsStill` exporta el frame graduado a resolución de timeline
- Funciona desde la Edit page (no hace falta cambiar a la Color page), con `.jpg` y `.tif`. Devuelve `False` si la carpeta de destino no existe.
- Sale a 1600×1080, la resolución del timeline, y con el grade (comprobado a ojo). JPG ~1 MB, TIF 8 bits ~10 MB.
- **No da frames atrasados**: el export justo después de `SetCurrentTimecode` es idéntico byte a byte al de un segundo después (6 de 6). Desde la Edit page y desde la Color page sale lo mismo.
- **Tiempo por frame (mover el cabezal + exportar JPG)**:
  - dentro de un plano: mediana ~500 ms, con saltos de 1, 5 o 12 frames (8 muestras por paso). Es muy constante, como si esperara un temporizador.
  - saltando de un clip a otro: 35–60 ms.
- Coste estimado para un timeline de 50 planos con 10 muestras por plano: ~4 min. Es viable, y además el owner aclaró que el objetivo es quitarse el rato de elegir el still a mano, no ir rápido.
- Sin verificar: que el frame exportado sea exactamente el del cabezal (sin desfase de un frame); que respete el viewer en bypass o con un wipe.

## Segunda tanda (con permiso del owner, mismo proyecto, solo lectura)

### Predicciones
- Desfase entre el frame exportado y el del cabezal: 0 frames.
- Los ~500 ms se van en exportar, no en mover el cabezal.

### H3 — El frame exportado es exactamente el del cabezal
- Método: 25 exports alrededor de 5 cortes (los dos últimos frames del plano A y los tres primeros del B). Cada uno se compara con los frames fuente ±3 del `.mov` (ProRes 4444, leído con ffmpeg). La comparación es una correlación de rangos de luma a 192×130, que aguanta el grade.
- Con la correspondencia **frame fuente = `GetLeftOffset()` + (frame de timeline − `GetStart()`)**, el mejor candidato está en desfase 0 en 24 de 25. El otro (91743) es un empate en un plano estático (0,944 frente a 0,944). En los planos con movimiento la diferencia es clara (0,997 frente a 0,969).
- En los cortes, el primer frame del plano B es del B y el último del A es del A.
- **`GetSourceStartFrame()` puede ser un frame menor que `GetLeftOffset()`** (p. ej. 438 frente a 439; parece un redondeo de subframes). Para calcular frames fuente se usa `GetLeftOffset()`.
- **Predicción cumplida.**

### H4 — El coste está en mover el cabezal, y es un suelo de ~0,5 s por frame
- Dentro de un plano: `SetCurrentTimecode` tarda ~470 ms y `ExportCurrentFrameAsStill` ~25 ms (8 muestras). Dos exports seguidos del mismo frame sin mover: 27 y 25 ms.
- Recorrer 6 planos × 4 frames en orden secuencial: 480 ms/frame; en orden intercalado (un frame de cada plano por vuelta): 499 ms/frame. **No ayuda.** Los saltos baratos de la primera tanda (35–60 ms) venían después de una pausa de 1 s: Resolve parece cobrar ~0,5 s por cada frame que muestra, toque el que toque.
- **Predicción fallida** (el coste no está en exportar). Consecuencia: el presupuesto es ~0,5 s × frames muestreados; elegir bien cuántos y cuáles importa más que el orden.

## Siguiente paso
1. Prueba de pesos: el owner elige a mano el still de unos planos y se compara.
2. Empezar el código que no necesita Resolve: puntuación de frames con tests e `install.command`.
3. (No bloquea) Ver si alguna opción de Resolve (calidad del viewer, proxies, render cache) baja el suelo de H4.
