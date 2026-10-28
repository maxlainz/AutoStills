# 06 — Auditoría del repo (2026-10-28)

**TL;DR.** Auditoría completa del repo. En este Mac (macOS 27.0.1) Apple Vision no detectaba ninguna cara y el error se tragaba en silencio (H16). El muestreo contaba muestras como si fueran frames (H17). Las pistas sin marcar no tapaban (D25). Todo arreglado junto con cinco limpiezas menores; `make ci` verde con 49 tests.

## H16 — Vision rechaza un `{}` de Python como opciones
- `uv run pytest tests/test_faces.py` en macOS 27.0.1 con pyobjc 12.2.2: 2 tests fallaban (`text_fraction` None). `VNImageRequestHandler.initWithData_options_(data, {})` lanza `NSInvalidArgumentException - key does not exist`; con `NSDictionary.dictionary()` o `None` funciona. El `uv.lock` no había cambiado desde v0.1.0, así que lo más probable es que fuera la actualización de macOS.
- `faces.analyze` se tragaba la excepción: todos los planos salían «sin cara». Ahora devuelve `error` y el worker lo marca como `error_vision:…`, que la ventana enseña en «con error».
- La CI corre en Linux y salta estos tests: el gate de verdad para Vision es `make ci` en el Mac.

## H17 — En el muestreo las reglas contaban muestras
- Sonda (plano de 300 frames, 12 muestras): `valid_mask` dejaba 10 de 12, porque `sample_frames` ya quita los bordes y `valid_mask` quitaba otro 10 % de las muestras. Unos 0,5 s por frame leído (H4): ~1 s perdido por plano.
- `MIN_FRAMING = 25` se medía en muestras: con 12, un plano muestreado daba siempre 1 encuadre (frames seguidos con el mismo movimiento de cámara daban 2).
- Arreglo: `analyse_shot` recibe el tramo del plano; `valid_mask`, `framings` y `_moving` miden en frames de timeline. Test: `test_sampled_shot_keeps_its_samples_and_framings`.
- Límite que queda: entre dos muestras puede haber casi 1 s, y el flujo óptico pierde movimientos grandes de cámara. El rasgo «quieto» mide el cambio entre muestras, no el motion blur.

## Otros cambios
- D25: tapan también los clips de vídeo de pistas sin marcar (no los fotogramas fijos) y los no seleccionados.
- `refresh()` no falla si el export desaparece.
- `first_frame()` en un solo sitio (lo usaban `pick_export` y «Elegir fichero…»).
- El progreso usa el paso en curso: se ve el % de la comprobación del export.
- Los ficheros de salida del worker se cierran en la ventana.
- Eliminados: `pitch` y `roll` (no se usaban), el `objs` de `read_items` (no se usaba), y la tolerancia a «no hay tests» del Makefile. La cara principal sale de `select.main_face` (antes se buscaba dos veces).

## Notas del vault
- Ninguna: no hay conceptos nuevos, y el área sigue pendiente del owner.

## Siguiente paso
- En Resolve: comprobar qué `Type` da un PNG de logo (D25) y relanzar en el timeline de prueba con caras.
- Sigue la prueba de pesos con los marcadores del owner.
