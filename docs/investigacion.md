# Investigación de arranque (2026-10-22)

**TL;DR.** Que Resolve decodifique y gradúe los frames (así sirve cualquier códec, también BRAW, R3D y ARRIRAW, y el still sale con el grade); analizarlos fuera de Resolve con un worker propio; capturar solo los ganadores con la API de stills. Para la cara y la estética, Apple Vision cubre casi todo sin descargar modelos, pero solo en macOS. Nada de esto está medido todavía: son hipótesis hasta la primera medida (norma `prediccion-antes-de-medir.md`).

Fuentes: API de scripting de Resolve 21.1 (stubs y README del MCP de Resolve, consultados en este Mac), changelog de Resolve 19→21.1, PyPI y las webs citadas. Lo marcado *(sin verificar)* no se ha comprobado.

## 1. Qué ofrece Resolve 21.1 por API

| Función | Para qué nos sirve |
|---|---|
| `Timeline.GetItemListInTrack`, `TimelineItem.GetStart/GetEnd` | Los planos ya vienen cortados: cada clip del timeline es un plano |
| `Timeline.SetCurrentTimecode(tc)` | Mover el cabezal al frame elegido |
| `Timeline.GrabStill()` → `GalleryStill` | Still a la Gallery del frame actual, con grade |
| `GalleryStillAlbum.SetLabel / ExportStills(stills, carpeta, prefijo, formato)` | Etiquetar y exportar los stills |
| `Project.ExportCurrentFrameAsStill(ruta)` | Exportar el frame actual a fichero sin pasar por la Gallery |
| `Timeline.GetCurrentClipThumbnailImage()` | Miniatura RGB 8 bit (base64) del frame actual en la Color page: **podría servir para analizar sin render ni decodificar nada fuera** *(tamaño y velocidad sin medir)* |
| `Timeline.GrabAllStills(1|2)` | Lo que ya hace Resolve: primer o frame central. Es lo que queremos superar |
| `MediaPoolItem.AnalyzeForIntellisearch(identifyFaces, isBetterMode)` (nuevo en 21) | Resolve detecta personas y caras, pero **no hay función para leer en qué frames** *(sin verificar a fondo)* |
| `Timeline.DetectSceneCuts()` | Para un máster plano sin cortes |
| Render jobs (`AddRenderJob`, `StartRendering`) | Sacar un proxy pequeño del timeline para analizarlo |

Python: Resolve 21.1 trae **su propio Python 3.14** (`ResolvePython`, sin `pip`), y desde 21.1 **los scripts Python son solo de Studio** ([CineD](https://www.cined.com/es/davinci-resolve-21-1-released-ai-assistant-integration-via-mcp-individual-hdr-trims-and-python-scripting-moves-to-studio/)). En 19/20 usaba el Python de python.org del sistema. Conclusión: el script dentro de Resolve, solo stdlib; las librerías de análisis, en un entorno aparte (lección ya aprendida en MHL MediaManagement).

## 2. Tres maneras de conseguir los frames

| Camino | Ventajas | Inconvenientes |
|---|---|---|
| **A. Miniaturas de la Color page** (`SetCurrentTimecode` + `GetCurrentClipThumbnailImage`) | Cero render, cero dependencias para leer el frame, con grade, cualquier códec | Resolución baja; mover el cabezal frame a frame puede ser lento; obliga a estar en la Color page |
| **B. Render de un proxy** (540p H.264/ProRes Proxy del timeline) y análisis del fichero | Cualquier códec, con grade, frames 1:1 con el timeline, resolución suficiente para caras | Un render previo (minutos en timelines largos); el análisis necesita un decodificador (OpenCV/ffmpeg) |
| **C. Leer el media original** con ffmpeg/OpenCV | Sin render | **No decodifica BRAW, R3D ni ARRIRAW**; sin grade; rutas de red |

Recomendación inicial: B como camino principal, A a medir y C descartado.

**Medido el 2026-10-22 (bitácora 01, D13):** A no sirve, porque la miniatura es fija por clip y de 576×324. Hay un cuarto camino, que es el elegido: **D. `Project.ExportCurrentFrameAsStill`** frame a frame. Da el frame graduado a resolución de timeline, en ~0,5 s, sin render y sin tocar la Gallery. Es exactamente el frame del cabezal (H3); el frame fuente es `GetLeftOffset()` + (frame − `GetStart()`); los ~0,5 s se van en mover el cabezal y son un suelo (H4).

## 3. Señales para puntuar un frame

| Señal | Cómo | Coste | Dependencia |
|---|---|---|---|
| Nitidez / desenfoque de movimiento | Varianza del laplaciano o Tenengrad (Sobel), en la cara si la hay o en la zona saliente | Muy bajo | numpy/OpenCV |
| Movimiento | Diferencia con los frames vecinos (flujo óptico Farneback como mejora) | Bajo | numpy |
| Exposición | Histograma de luma: % quemado (>250) o empastado (<5) | Muy bajo | numpy |
| Evitar transiciones | Descartar el primer y último ~10 % del plano | Nulo | — |
| Caras | Apple Vision `VNDetectFaceRectanglesRequest`; OpenCV YuNet (230 KB, MIT) fuera de Mac | Bajo | pyobjc-framework-Vision / OpenCV |
| Calidad de la cara | Vision `VNDetectFaceCaptureQualityRequest` (0–1) | Bajo | pyobjc |
| Ojos abiertos | Landmarks de Vision → apertura del ojo (EAR); MediaPipe da `eyeBlink` directo | Bajo | pyobjc / MediaPipe |
| Estética global | Vision `VNCalculateImageAestheticsScoresRequest` (macOS 15+) | Bajo | pyobjc |
| Estética (modelo) | LAION aesthetic predictor (CLIP ViT-L/14, ~900 MB, torch) | Alto | torch |
| Composición | Saliencia de Vision (`VNGenerateAttentionBasedSaliencyImageRequest`) | Bajo | pyobjc |

La nitidez se compara **dentro del plano** (ranking), nunca en absoluto: depende del contenido y el grano la infla.

Descartados para empezar: pyiqa (BRISQUE/NIQE/MUSIQ; licencia PolyForm Noncommercial y torch) e InsightFace (modelos solo para investigación no comercial).

## 4. Precedentes
- **Yahoo Hecate** (Apache-2.0, sin mantenimiento; Song et al., CIKM 2016): detecta planos → quita frames borrosos, oscuros y de transición → agrupa → ranking estético. Es el esquema a copiar.
- **YouTube** (2015): red entrenada con miniaturas elegidas a mano tras un filtro barato *(sin verificar la URL)*.
- **ffmpeg `thumbnail`**: el frame más «representativo» por histograma; mide representatividad, no calidad.
- No se ha encontrado ningún script público de Resolve que elija stills por calidad (búsqueda ligera).

## 5. Stack candidato para v0.1 (pendiente del owner)
1. Script en Resolve, solo stdlib (UIManager): lee los planos, saca los frames (camino A o B), lanza el worker, recibe las puntuaciones, mueve el cabezal a los ganadores y hace `GrabStill` en un álbum nuevo (y opcionalmente `ExportStills`).
2. Worker en un entorno de `uv` creado por el instalador: `numpy` + `opencv-python-headless` + `pyobjc-framework-Vision` (licencias permisivas, ~60 MB, sin descargar modelos). Puntúa nitidez, movimiento, exposición y, en macOS 15+, cara, ojos y estética; suma ponderada y ranking por plano.

Después: YuNet/MediaPipe para Windows/Linux, PySceneDetect para planos largos, LAION como descarga opcional, varios stills por plano con diversidad, presets de pesos (Gallery de referencia vs miniatura para redes).

## 6. Modelos de decisión JEV (investigado el 2026-10-22, a petición del owner)

**TL;DR.** JEV no describe imágenes ni genera texto: dada una imagen y una pregunta con opciones cerradas, devuelve **probabilidades calibradas** («¿cuál de estos frames es mejor still?» → 0,53 / 0,33 / 0,14). Encaja como **juez final** sobre 3–5 candidatos por plano, no como filtro de todos los frames. Hay versiones abiertas con visión (Apache-2.0), pero su runtime principal es vLLM con GPU NVIDIA: **en Mac no está probado** y el modelo pesa ~18 GB. Decisión (D16): no entra en v0.1; se explora después, sobre una preselección, frente a un VLM local con MLX.

| | Jev (TypeSafe AI) | JEV-9B / JEV-27B-VL (AutoTrust AI Lab) |
|---|---|---|
| Qué es | Modelo de decisión cerrado, lanzado en septiembre de 2026 | Destilados abiertos de Jev sobre Qwen3.5-9B / Qwen 27B; no afiliados a TypeSafe |
| Visión | No mencionada | Sí, *zero-shot*: imágenes en base64 dentro del `state` (JEV-9B desde el 2026-10-03; JEV-27B-VL) |
| Preguntas | Clasificación, puntuación | `noul` (sí/no), `choice` (2–16 opciones), `score` (0–5 con distribución y valor esperado) |
| Local | No: solo API (en la nube) | Pesos descargables (~18 GB en BF16 para 9B); GGUF de terceros (Q3 de 4,6 GB, «baja calidad») |
| Runtime | API | vLLM (recomendado, GPU), `transformers` + `peft`. **MLX, llama.cpp y Apple Silicon no aparecen en la ficha** |
| Velocidad | 238–301 ms por decisión (API) | ~90 ms por decisión en una B200; ~0,2 s por decisión con imagen |
| Licencia | Comercial | Apache-2.0 (los modelos base mantienen la suya) |

**Cómo encajaría.** Los criterios baratos de `docs/criterios.md` sacan 3–5 candidatos por plano y JEV elige entre ellos (`choice`) o puntúa cada uno (`score`). Sería otra señal, con peso propio en los presets.

**Pegas**
- La API de TypeSafe sube los frames a la nube. Con material de cliente, eso es un problema de confidencialidad: se descarta.
- La ficha de JEV-9B advierte de un sesgo de orden: con 16 opciones, cambiar solo el orden cambia el 11,5 % de las respuestas. Habría que barajar las opciones y promediar.
- No hay evidencia de que la vía de visión funcione en Mac fuera de vLLM.
- Es otra descarga grande, que choca con D11 (instalación fácil). Las cifras de las fichas son autodeclaradas.

**Alternativa a comparar.** Un VLM general local con MLX (familia Qwen-VL o Gemma, en 4 bits) al que se le pregunta lo mismo. Está más maduro en Mac, pero no da probabilidades calibradas.

Fuentes: [ficha de JEV-9B](https://huggingface.co/autotrust/JEV-9B), [organización autotrust](https://huggingface.co/autotrust), [GGUF de terceros](https://huggingface.co/prithivMLmods/JEV-9B-GGUF), [TechCrunch sobre Jev](https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/), [JevLite (solo texto, Core ML)](https://huggingface.co/j-llm/jevlite), [JEVQA, Jev como predictor de calidad de vídeo](https://arxiv.org/pdf/2609.24395).
