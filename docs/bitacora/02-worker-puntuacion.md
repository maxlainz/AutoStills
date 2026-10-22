# 02 — Worker de puntuación (2026-10-22)

**TL;DR.** Primer código: el worker que puntúa frames y elige stills (`autostills/`), sin Resolve, con 24 tests sobre frames sintéticos y una revisión adversarial aplicada. En un clip real del owner encuentra la cara, los ojos y la orientación, y analiza 88 frames en 4,5 s (H5). La ventana dentro de Resolve y `install.command` todavía no existen.

## Qué se hizo
- `autostills/metrics.py`: métricas baratas por frame (criterios 1–3, 14–16) y `difference()` para comprobar que el export cuadra con Resolve (D17).
- `autostills/select.py`: ranking dentro del plano, filtro de bordes, flashes y negros (criterio 5), estabilidad del foco (criterio 4), rasgos de cara (criterios 6–11), composición (12), texto (20), presets con pesos provisionales y elección de N stills con diversidad (18).
- `autostills/faces.py` (delegado en un subagente): Apple Vision con una sola petición por frame (caras + landmarks, calidad de cara, saliencia, texto, estética opcional). En Linux importa sin Vision y devuelve vacío.
- `autostills/worker.py`: `python -m autostills.worker job.json result.json`. Lee el export una sola vez (o los frames muestreados), hace dos pasadas por plano y escribe el progreso en stdout.
- Dependencias: `numpy`, `opencv-python-headless` 5.0, `pyobjc-framework-Vision` (solo macOS). `pythonpath = ["."]` para pytest.
- Un bug encontrado por los tests: el detector de flashes comparaba con la mediana del plano y tiraba precisamente el frame bien expuesto de un plano casi todo quemado. Ahora busca picos aislados respecto a los dos vecinos.

## H5 — Velocidad (medido el 2026-10-22, Mac Studio, macOS 26.3)
- OpenCV decodifica ProRes 4444 de 2048×1152 a **3,5 ms por frame** (100 frames de un `.mov` del proyecto). Un export de ~5 500 frames se lee en ~20 s.
- Vision (`faces.analyze`) tarda **28 ms** por frame a 1600×1080 y 12 ms a 960×540; con estética, +3–5 ms (medido por el subagente sobre frames sintéticos).
- Worker entero sobre un clip real sin gradear (88 frames, preset gallery, N = 3): **4,5 s**, arranque incluido.
- Predicción: no había ninguna escrita antes. Fallo de método, anotado aquí.

## Prueba con una cara real (solo lectura; los frames se borraron)
- Clip de un plano medio de una persona sentada. Vision detecta la cara en los 8 candidatos; `eyes_open` sale entre 0,62 y 0,92 y la orientación entre −45° y −90°, valores que parecen venir cuantizados de Vision.
- Los 3 elegidos tienen la cara levantada y legible; los frames del borde del plano (mirando abajo, mano en movimiento) quedan fuera. Es una impresión a ojo; la validación de verdad es la prueba de pesos.

## Revisión adversarial (subagente Opus) y correcciones
- Verificado sin fallos: la correspondencia frame de vídeo → frame de timeline y los límites de plano (fin exclusivo, planos solapados, planos antes, a caballo o después del vídeo, un plano que acaba en el último frame).
- Corregido:
  1. Un frame ilegible tumbaba todo el trabajo sin escribir `result.json`. Ahora se salta con el aviso `frames_ilegibles:N`, y un error en un plano queda en ese plano (`error:…`).
  2. Los rasgos con sentido absoluto (ojos, calidad de cara, boca, orientación, texto, exposición, composición, estética) se rankeaban, así que una cara con los ojos cerrados no perdía puntos si era la única del plano. Ahora conservan su valor 0..1, y que haya cara suma (`face_present`).
  3. `n` quedaba limitado a 8 en silencio: ahora hay al menos `n` candidatos.
  4. Si Vision fallaba, el frame contaba como «sin texto», la mejor nota posible. Ahora queda en None y no resta.
  5. Un frame corrupto en el export cortaba la lectura. Ahora se toleran hasta 5 seguidos antes de darlo por acabado.
  6. Una caja de cara fuera del cuadro hacía fallar la nitidez de la cara: ahora da None.
  7. Las cajas de texto pegadas al borde superior o izquierdo se perdían.
- Hay 4 tests de regresión nuevos (24 en total). En el clip real se mantienen los frames 380 y 412; el tercero pasa del 390 al 399.

## Ventana de Resolve e instalador
- `AutoStills.py`: la ventana del boceto D15 con la fila «Fuente» (D17). Solo stdlib y un temporizador, así que Resolve no se congela mientras lee frames o analiza. La lógica pura (planos visibles por pista, clips repetidos, marcadores, último export, muestreo, timecode) tiene tests en `tests/test_gui.py`.
- El worker gana el modo `check` (diferencia entre el export y Resolve, D17) y la mezcla por plano: un plano con sus propios frames se analiza con ellos aunque la fuente sea el vídeo.
- `install.command`: instala uv si falta, copia el script a `Scripts/Utility` y crea el entorno en `~/Library/Application Support/AutoStills/.venv` (176 MB). Probado con una carpeta de usuario falsa: Apple Vision disponible.
- **Sin probar dentro de Resolve.** Supuestos que hay que verificar en la primera prueba:
  1. las claves de `TimelineItem.GetMarkers()` son offsets desde el inicio del clip;
  2. `GrabStill` necesita la Color page;
  3. `MarkIn` de un trabajo de render es el frame de timeline del primer frame del fichero;
  4. el umbral de 0,03 de la comprobación del export (frame graduado de Resolve frente al render);
  5. el temporizador de UIManager dispara con `disp.On.Timeout` o con `disp.On.Tick.Timeout`.

## Pendiente
- Prueba de pesos con los marcadores del owner en una copia del timeline.
- Comprobar en Resolve que la cola de render conserva los trabajos y da la ruta completa del fichero (D17).
- Las constantes de ojos (`EAR_CLOSED`, `EAR_OPEN`) son a ojo; se ajustan con la prueba de pesos.

## Siguiente paso
1. Primera prueba del owner en Resolve (supuestos de arriba).
2. Prueba de pesos con los marcadores del owner.
