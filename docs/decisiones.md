# Decisiones

Una entrada por decisión: contexto, opciones, elección, fecha. Nunca se borra ni se renumera una decisión: se marca **sustituida por Dn**. Las decisiones vienen de la entrevista con el owner (norma `entrevista.md`) o de hallazgos medidos (`Hn`, en la bitácora).

## D1 — Nombre: AutoStills
- **Contexto**: el owner creó la carpeta `AutoStills` para el proyecto.
- **Elección**: **AutoStills** (carpeta, repo y, en Resolve, Workspace › Scripts › «AutoStills»).
- 2026-10-22.

## D2 — Método de la familia de repos
- **Contexto**: los repos del owner comparten método; MHL MediaManagement (script de Resolve) es la plantilla más cercana.
- **Elección**: router `CLAUDE.md`, normas en `.claude/rules/`, hooks en `.claude/settings.json`, `docs/decisiones.md`, `docs/bitacora/`, `CHANGELOG.md` (Keep a Changelog), `Makefile` con `make ci`, CI en GitHub Actions.
- 2026-10-22. El owner pidió «sus normas y documentación estándar» mirando sus otros repos.

## D3 — Repo público en GitHub, licencia MIT
- **Contexto**: el resto de la familia es público y MIT.
- **Elección**: público desde el primer push (`maxlainz/AutoStills`), MIT.
- 2026-10-22, entrevista de alcance.

## D4 — Nada del estudio entra en el repo
- **Elección**: ni nombre del estudio, ni clientes, ni rutas, ni IPs, ni material real (norma `repo-publico.md`, `make leak-check`).
- 2026-10-22, heredado de la familia.

## D5 — Git y versiones
- **Elección**: Conventional Commits en inglés con scope; SemVer desde `v0.1.0`; Keep a Changelog en español; sin trailers de atribución; nunca se commitea en `main` (rama + PR + CI verde) salvo el commit inicial del arranque.
- 2026-10-22, heredado de la familia.

## D6 — Usos: varios, con presets
- **Contexto**: los stills pueden servir de Gallery de referencia (calidad técnica), de miniaturas/redes (estética) o de contact sheet (representatividad).
- **Elección**: **todos**; la ventana ofrece presets que cambian los pesos de las señales. Qué presets y con qué pesos se decide al implementar, con boceto previo (norma `entrevista.md`).
- 2026-10-22, entrevista de alcance.

## D7 — Criterios de la primera versión
- **Elección**: nitidez y poco motion blur, caras con ojos abiertos, exposición, y estética/composición. **La estética es experimental**: entra solo tras probarla contra stills elegidos por el owner (predicción y medida, norma `prediccion-antes-de-medir.md`).
- 2026-10-22, entrevista de alcance.

## D8 — Salida: álbum nuevo de la Gallery
- **Opciones**: álbum de la Gallery; Gallery + ficheros; solo ficheros.
- **Elección**: un **álbum nuevo de la Gallery** por ejecución, cada still etiquetado con el nombre del plano. Exportar a fichero queda fuera de v0.1.
- 2026-10-22, entrevista de alcance.

## D9 — Plataforma: solo macOS + Resolve Studio 21.1 o posterior
- **Contexto**: desde 21.1 Resolve trae Python 3.14 propio y los scripts Python son solo de Studio; Apple Vision da caras, calidad de cara, landmarks, saliencia y estética sin modelos (`docs/investigacion.md`).
- **Elección**: solo Mac, Resolve Studio ≥ 21.1. Se puede usar Apple Vision (pyobjc). Windows y Resolve 19/20, fuera.
- 2026-10-22, entrevista de alcance.

## D10 — Stills por plano: 1 por defecto, ajustable (**sustituida por D19**)
- **Elección**: 1 por defecto, ajustable en la ventana (1–5). Con más de uno, frames distintos entre sí (no consecutivos casi iguales).
- 2026-10-22, entrevista de alcance.

## D11 — Instalación: un paso, con un entorno aislado de uv
- **Opciones**: instalador de un paso con `uv`; `.pkg` de macOS; sin dependencias.
- **Elección**: `install.command` (doble clic) que copia el script a Resolve y crea con `uv` un entorno aislado con las librerías de análisis (numpy, OpenCV, pyobjc-framework-Vision). No toca el Python del sistema ni el de Resolve. La GUI dentro de Resolve sigue siendo solo stdlib y lanza el worker con ese entorno (norma `resolve.md`).
- 2026-10-22, entrevista de alcance.

## D12 — GitHub: `main` protegida, CI obligatoria y seguridad del repo público
- **Contexto**: el repo es público (D3); el owner pidió protección de rama, CI «y demás».
- **Elección** (igual que MHL MediaManagement, más Dependabot):
  - `main` protegida: check `ci` obligatorio y al día con `main` (strict), historial lineal, conversaciones resueltas, sin force-push ni borrado, **también para admins**. Sin revisor obligatorio mientras escriba una sola persona.
  - Merge solo por squash o rebase (sin merge commits), auto-merge permitido, ramas borradas al mergear; sin wiki ni projects.
  - Secret scanning y push protection activados; alertas de vulnerabilidades activadas; Dependabot semanal para las actions y las dependencias de uv (`.github/dependabot.yml`).
- 2026-10-22. El owner autorizó mergear los PR con CI verde.

## D13 — Frames para analizar: `ExportCurrentFrameAsStill`, a resolución de timeline
- **Contexto**: hacía falta elegir cómo obtener los frames (`docs/investigacion.md` §2). Medida de la bitácora 01: la miniatura de la Color page es fija por clip y de 576×324 (H1); `ExportCurrentFrameAsStill` da el frame graduado a resolución de timeline, sin frames atrasados, en ~0,5 s (H2).
- **Opciones**: miniaturas de la Color page; render de un proxy; `ExportCurrentFrameAsStill` frame a frame.
- **Elección** (**matizada por D17**: ahora es la fuente secundaria): **`ExportCurrentFrameAsStill`** desde la Edit page, a una carpeta temporal, a resolución de timeline. Descartadas las miniaturas: baja resolución, y no todo son primeros planos (owner). El proxy queda como plan B si un timeline largo lo hace necesario.
- 2026-10-22. El owner confirmó que la resolución baja no basta y que el objetivo es quitarse el rato de elegir el still a mano.

## D14 — Los 20 criterios de selección entran en v0.1
- **Contexto**: brainstorming de criterios con el owner (`docs/criterios.md`). Amplía D7.
- **Opciones**: por familias (técnicos, personas, composición/estética, colorista, reglas de flujo).
- **Elección**: **todos**: nitidez, movimiento, exposición, rack focus, bordes del plano; presencia de caras, ojos, boca, orientación, cara completa, calidad de cara; saliencia, estética (a prueba, D7); representativo del grade, rango tonal, piel visible; los marcadores mandan, diversidad con N stills, no duplicar clips repetidos, saltar títulos/generadores/texto. El owner no añade más por ahora.
- 2026-10-22.

## D15 — Boceto de la ventana aprobado (**sustituido por D18**)
- **Contexto**: el boceto en texto del 2026-10-22 (norma `entrevista.md`): timeline y número de planos; preset (Gallery de referencia · Miniatura/redes · Contact sheet); stills por plano; pistas; todo el timeline o clips seleccionados; «Marcadores mandan» con su color; ajustes avanzados plegados (pesos); nombre del álbum; barra de progreso con plano actual y tiempo restante; Cancelar / Sacar stills. Al terminar, un resumen: planos sin cara, sin ningún frame nítido y resueltos por marcador. Cada still se etiqueta «CLIP · TC».
- **Elección**: **aprobado por el owner** tal cual. Cualquier cambio posterior se enseña antes como boceto.
- 2026-10-22.

## D16 — Modelos de decisión JEV: a explorar en el futuro, sobre una preselección
- **Contexto**: investigación del 2026-10-22 (`docs/investigacion.md` §6).
- **Elección**: **fuera de v0.1; se explora después** como juez final que elige entre 3–5 candidatos preseleccionados por los criterios baratos, no sobre todos los frames. Al owner le «pinta muy interesante» sobre una preselección. La API en la nube de TypeSafe queda descartada por confidencialidad.
- 2026-10-22.

## D17 — Fuente de análisis: el último export del timeline (mejor) o muestreo desde el timeline
- **Contexto**: con el suelo de ~0,5 s por frame (H4), muestrear 10 frames por plano puede quedarse corto. Propuesta del owner: analizar un render ya hecho del timeline entero, así se puntúan **todos** los frames. El still final sale igualmente de Resolve con Grab Still en el frame ganador.
- **Opciones**: solo export; export + muestreo; export + render de análisis nuevo + muestreo.
- **Elección**:
  - **Dos fuentes en la ventana**: «Desde el último export (mejor)», por defecto, y «Desde el timeline (muestreo)» (D13). Un render nuevo de análisis queda fuera, para no tocar la cola de render.
  - **Qué cuenta como último export**: un trabajo de la cola de render de este timeline, completo, en un solo clip, que cubra el timeline entero y cuyo fichero exista. Si hay varios, el más reciente por fecha del fichero. La API no da la fecha de render ni dice si hubo flat pass.
  - **Sin export válido**: diálogo para elegir el fichero a mano; si se cancela, se pasa a muestreo.
  - **Comprobación previa**: 1 frame por plano exportado desde Resolve se compara con el mismo frame del render. Caza un grade cambiado, un montaje cambiado o un flat pass.
  - **Si algunos planos no cuadran**: se mezcla. Los que cuadran se analizan con el export y los demás por muestreo; el resumen final dice qué vía usó cada plano.
  - **Coste**: dos pasadas. Lo barato (nitidez, movimiento, exposición) en todos los frames; caras y estética en los mejores de cada plano.
- 2026-10-22. Cambia el boceto de la ventana (D15): fila nueva «Fuente», pedida por el owner.

## D18 — Ventana v2: tres pasos y botón «Analizar»
- **Contexto**: primera impresión del owner al verla: no está claro qué paso va, y «Sacar stills» suena a exportar.
- **Elección** (boceto aprobado tal cual):
  - Tres bloques numerados: **1 · Qué planos** (pistas, todo o seleccionados), **2 · Cómo elegir** (preset, stills por plano de mín a máx, fuente, respetar marcadores con su color) y **3 · Qué hacer con los elegidos** (marcar en el timeline, añadir a la Gallery con su álbum).
  - Barra con el paso en curso: 1 Comprobar el export · 2 Analizar · 3 Marcar o añadir · 4 Listo.
  - Botón **«Analizar»** y un resumen final con lo que se ha hecho.
- 2026-10-22. Sustituye a D15.

## D19 — Stills por plano: de 0 a X (por defecto 0–3)
- **Contexto**: un plano corto que es poco más que motion blur no debería dar still, y un plano largo con la cámara en movimiento puede tener varios encuadres. Sustituye a D10.
- **Elección**: mínimo y máximo en la ventana, **0 y 3 por defecto**.
  - **0 stills** si el plano es muy corto, o si su mejor frame queda claramente por debajo, en nitidez, de los planos normales **del mismo timeline**. La puntuación dentro del plano es relativa, así que hace falta esa comparación con el resto.
  - **Más de 1** solo si el plano tiene encuadres claramente distintos: los frames se agrupan por composición a lo largo del tiempo y sale como mucho uno por grupo.
  - Los umbrales son provisionales hasta la prueba con el owner.
- 2026-10-22.

## D20 — Marcadores en el timeline como salida, y se respetan al relanzar (**matizada por D23**: van en el timeline, no en el clip)
- **Contexto**: propuesta del owner. Si un pase deja marcadores, los siguientes no tienen que analizar, y el owner puede corregir a mano.
- **Elección**:
  - **Salida por defecto: solo marcadores** en el clip, del color elegido, con la marca `AutoStills` en sus datos y la puntuación en la nota. Añadirlos a la Gallery es una casilla aparte. Flujo típico: un pase marca, el owner revisa y corrige, y un segundo pase con «Añadir a la Gallery» ya no analiza.
  - **Al relanzar se respetan**: un plano con algún marcador del color elegido (de AutoStills o del owner) no se analiza, y sus marcadores son sus stills. Para reanalizar un plano, se borran sus marcadores.
- 2026-10-22.

## D21 — Nombre de stills y marcadores: REC TC primero (**matizada por D24**)
- **Contexto**: con el nombre del clip delante, los stills se ordenan por nombre de clip, que es arbitrario.
- **Elección**: **«REC TC · CLIP»** (timecode del timeline y nombre del clip sin extensión), para la etiqueta del still y el nombre del marcador. Así salen en el orden de la peli.
- 2026-10-22.

## D22 — «Guardar como predeterminado»
- **Elección**: un botón discreto en la esquina de la ventana guarda los ajustes actuales (pistas, todo o seleccionados, preset, mínimo y máximo, fuente, respetar marcadores, color, salidas) en `~/Library/Application Support/AutoStills/settings.json`. La ventana los carga al abrirse.
- 2026-10-22.

## D23 — Los marcadores van en el timeline, no en el clip
- **Contexto**: primera prueba del owner. La v2 los ponía en el clip (`TimelineItem.AddMarker`), y el owner los quiere en el timeline.
- **Elección**: `Timeline.AddMarker`, con el mismo color, nombre «REC TC · CLIP», nota y `customData` `AutoStills`. Al relanzar se leen los marcadores del timeline (`Timeline.GetMarkers`) del color elegido dentro del tramo visible de cada plano. Los marcadores de clip ya no cuentan.
- Limpieza: a petición del owner se borraron los 54 marcadores de clip que había dejado la v2 en el timeline de prueba (todos con `customData` `AutoStills`; no había otros).
- 2026-10-22.

## D24 — Frame absoluto al principio del nombre
- **Contexto**: Frame.io no ordenaba bien los stills por TC.
- **Elección**: **«0090217 · 01:00:08:17 · CLIP»**: el frame absoluto del timeline con 7 cifras (orden alfabético = orden de la peli en cualquier herramienta), luego el REC TC y el clip. Para stills y marcadores.
- 2026-10-22.

## D25 — Qué tapa a un plano: también las pistas sin marcar, salvo los fotogramas fijos
- **Contexto**: auditoría del 2026-10-28. Solo tapaban los clips de las pistas marcadas. Con una entrevista en V1 y B-roll en V2 sin marcar, se puntuaba el B-roll (es lo que sale en el export y en los frames de Resolve) y después Grab Still apagaba V2 y sacaba la entrevista en un frame que nadie había mirado. Con logos y textos en PNG (bitácora 05) sí interesa que no tapen.
- **Opciones**: (a) como estaba; (b) todo clip con media tapa; (c) un clip de vídeo de una pista sin marcar tapa, un fotograma fijo no.
- **Elección**: **(c)**, la recomendación de la auditoría, aceptada por el owner («fix all»). Se distingue por la propiedad `Type` del clip del Media Pool (tapa si contiene «Video»). Con «Clips seleccionados», los no seleccionados también tapan. Pendiente de comprobar en Resolve qué `Type` da un PNG.
- 2026-10-28.

## Pendientes
- Pesos de cada preset (D6) y frames muestreados por plano: con una prueba contra stills elegidos por el owner.
