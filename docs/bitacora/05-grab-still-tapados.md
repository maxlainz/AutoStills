# 05 — Grab Still de planos tapados (2026-10-23)

**TL;DR.** En timelines con gráficos encima de los planos (logo en V3 durante casi todo el spot, textos en V2) solo salía el still del único plano sin nada encima: 1 de 14. Desactivar los clips de encima funcionaba; lo que fallaba era la comprobación posterior. Arreglado y probado en Resolve: 14 de 14, limpios.

## H15 — En la Color page `GetCurrentVideoItem()` no ve los clips desactivados
- Timeline de prueba del owner: planos en V1, PNG de texto en V2 sobre casi todos, un logo en V3 que cubre del frame 0 al 412 de 500. La ejecución anterior marcó 14 frames y sacó 1 still: el del frame 487, el único sin nada encima.
- Medido con el MCP de Resolve en ese timeline, reactivando todo en un `finally` (al acabar: ningún clip desactivado, cabezal y página como estaban, ningún still de más en la Gallery):
  - En Edit, tras `SetClipEnabled(False)` en V2 y V3, `GetCurrentVideoItem()` pasa al clip de V1 al instante.
  - En la Color page sigue devolviendo el logo: después de mover el cabezal 1 frame, después de esperar 0,5 s e incluso yendo a otro plano que siga bajo el logo. Solo se actualiza si el cabezal pasa por un frame donde el current sea otro clip.
  - Pero `GrabStill()` sí saca el still de V1. Sin desactivar nada, el still lleva el logo quemado; con el logo desactivado y sin mover nada más, sale limpio (comprobado exportando los stills con `ExportStills` y mirándolos).
- Así que `grab_from` desactivaba bien los clips de encima, preguntaba a `GetCurrentVideoItem()`, recibía el logo y se rendía con «otro clip encima que no se pudo apartar», sin llegar a intentar el still.
- Arreglo: `grab_from` ya no pregunta a `GetCurrentVideoItem()`. Siempre desactiva los clips de las pistas de encima en ese frame (también si son transparentes: el still los quema igual), saca el still y los reactiva. Solo se rinde si `SetClipEnabled(False)` falla.
- Resultado con la lógica nueva sobre los 14 marcadores: 14 de 14 stills, ninguno con texto o logo encima, en 7,6 s.

## Tests
- `grab_still` y `grab_from` salen de `gui()` al nivel del módulo (reciben el timeline) para probarlos sin Resolve con un timeline falso en `tests/test_gui.py`: apaga solo los clips de encima que tapan el frame y los deja como estaban (también los que ya estaban apagados), no toca las pistas de debajo, reintenta `GrabStill`, se rinde si un clip no se deja apagar y lo restaura todo aunque Resolve lance una excepción. El timeline falso no tiene `GetCurrentVideoItem`, así que si alguien vuelve a usarlo los tests fallan (H15).

## Siguiente paso
- Que el owner relance AutoStills con la Gallery activada en ese timeline.
- Sigue la prueba de pesos con los marcadores del owner (bitácora 04).
