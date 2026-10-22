# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado: [SemVer](https://semver.org/lang/es/). Categorías: Añadido · Cambiado · Corregido · Decidido · Medido · Eliminado.

## [Unreleased]
### Corregido
- El último export no se encontraba: el fichero estaba en una subcarpeta que la API no da (H6), y `MarkIn` no es el rango renderizado (H7). Ahora se busca en subcarpetas y el inicio se lee del timecode del `.mov`; ya no hace falta que el render cubra todo el timeline (bitácora 03).

### Cambiado
- Los marcadores van en el timeline, no en el clip, y al relanzar se leen del timeline (D23).
- «Guardar ajustes como predeterminados» pasa a un botón «⋯» en la esquina.

### Añadido
- Ventana v2 (D18): tres pasos, paso en curso, botón «Analizar». Marcadores en el timeline como salida por defecto y se respetan al relanzar (D20). De 0 a X stills por plano, uno por encuadre, con descarte de planos cortos o blandos (D19). Nombre «REC TC · CLIP» (D21). «Guardar como predeterminado» (D22).
- Ventana de Resolve `AutoStills.py` (D15, D17): preset, stills por plano, pistas, todo o selección, fuente (último export o muestreo), marcadores, álbum; comprueba el export plano a plano, mezcla export y muestreo, hace Grab Still con etiqueta «CLIP · TC» y deja cabezal y página como estaban.
- `install.command` de un doble clic (D11).
- Worker de puntuación `autostills/` (bitácora 02): métricas baratas, Apple Vision (caras, ojos, boca, orientación, saliencia, texto, estética opcional), presets con pesos provisionales, elección de N stills con diversidad; lee el export una sola vez o frames muestreados; tolera frames ilegibles y errores por plano. 24 tests sobre frames sintéticos.
- Arranque del repo con el método de la familia: normas, hooks, skills, `make ci`, CI, `leak-check` (bitácora 00).
- Investigación de opciones: API de Resolve 21.1, caminos para obtener frames, señales de puntuación, precedentes (`docs/investigacion.md`).

### Añadido (GitHub)
- `main` protegida, secret scanning, alertas de vulnerabilidades y Dependabot (D12).

### Añadido (criterios)
- `docs/criterios.md`: los 20 criterios de selección en cinco familias, cómo medir cada uno y los presets (D14).

### Añadido (investigación)
- Modelos de decisión JEV (TypeSafe y AutoTrust) como posible juez final: `docs/investigacion.md` §6.

### Medido
- H8: OpenCV decodifica el render H.265 10 bits 1600×1080 a 2 ms por frame (bitácora 03).
- H5: OpenCV decodifica ProRes 4444 2K a 3,5 ms/frame; Vision 28 ms/frame a 1600×1080; 88 frames reales en 4,5 s (bitácora 02).
- H1: la miniatura de la Color page es fija por clip y de 576×324. H2: `ExportCurrentFrameAsStill` da el frame graduado a resolución de timeline en ~0,5 s, sin frames atrasados (bitácora 01).
- H3: el frame exportado es exactamente el del cabezal; frame fuente = `GetLeftOffset()` + (frame − `GetStart()`). H4: ~0,5 s por frame, que se van en mover el cabezal; intercalar planos no ayuda (bitácora 01).

### Decidido
- D1 (nombre AutoStills), D2 (método de la familia), D3 (público, MIT), D4 (nada del estudio en el repo), D5 (git y versiones).
- Entrevista de alcance: D6 (varios usos con presets), D7 (nitidez, caras y ojos, exposición; estética experimental), D8 (álbum nuevo de la Gallery), D9 (solo Mac + Resolve Studio 21.1+), D10 (1 still por plano, ajustable), D11 (instalador de un paso con uv), D12 (protección de `main` y seguridad del repo), D13 (frames con `ExportCurrentFrameAsStill`), D14 (los 20 criterios en v0.1), D15 (boceto de la ventana aprobado), D16 (JEV a explorar en el futuro sobre una preselección), D17 (fuente: último export del timeline o muestreo, con mezcla por plano), D18–D22 (ventana v2, 0–X stills, marcadores, REC TC primero, ajustes predeterminados), D23 (marcadores en el timeline).
