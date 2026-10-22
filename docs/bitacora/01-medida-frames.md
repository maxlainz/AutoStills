# 01 — Medida: cómo sacar los frames de Resolve (2026-10-22)

**TL;DR.** La miniatura de la Color page no sirve: es fija por clip y de 576×324 (H1). `Project.ExportCurrentFrameAsStill` sí: exporta el frame del cabezal **graduado y a resolución de timeline**, desde la Edit page, sin tocar el proyecto ni la Gallery. Tarda ~0,5 s por frame dentro de un plano y no da frames atrasados (H2). Decisión: D13.

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

## Siguiente paso
1. Boceto de la ventana y de los presets (D6) para que el owner lo apruebe.
2. Verificar que no hay desfase de frame (exportar frames consecutivos de un contador o de un clip de prueba).
3. Probar si los ~500 ms dentro de un plano se pueden bajar (exportar en orden, otro formato, otra página). No bloquea.
