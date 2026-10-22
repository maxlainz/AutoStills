# Criterios de selección

**TL;DR.** Hay 20 criterios en cinco familias, y el owner los quiere todos en v0.1 (D14). Los criterios A, B, C y D **puntúan** cada frame muestreado de un plano. Los E son **reglas** que deciden qué se analiza y cómo se reparten los stills. Los presets (D6) son juegos de pesos sobre la puntuación. Los pesos se fijan probando contra stills elegidos por el owner.

Una regla para todas las métricas: **se comparan dentro del plano** (ranking), nunca en absoluto, porque dependen del contenido. Una señal que no aplica (no hay cara, no hay piel) **no resta**: su peso se reparte entre las demás.

## A. Técnicos — descartar frames malos
| # | Criterio | Cómo (propuesta) | Herramienta |
|---|---|---|---|
| 1 | Nitidez | Varianza del laplaciano / Tenengrad, en la cara si la hay o en la zona saliente | OpenCV |
| 2 | Movimiento | Diferencia con los frames vecinos; flujo óptico si hace falta | numpy / OpenCV |
| 3 | Exposición | % de luma > ~250 o < ~5 | numpy |
| 4 | Rack focus | Curva de nitidez de la zona saliente a lo largo del plano; se prefiere el frame donde se estabiliza en el máximo | OpenCV |
| 5 | Bordes del plano | Fuera el primer y último ~10 %; fuera frames negros y saltos bruscos de luma media (flash, fundido) | numpy |

## B. Personas
| # | Criterio | Cómo | Herramienta |
|---|---|---|---|
| 6 | Presencia de caras | Número y tamaño de caras; suma si hay, no obliga | Vision `VNDetectFaceRectanglesRequest` |
| 7 | Ojos abiertos | Apertura del ojo (EAR) con los landmarks | Vision landmarks |
| 8 | Boca | Apertura de la boca: evitar la media sílaba | Vision landmarks |
| 9 | Orientación | Yaw/pitch/roll de la cara; frontal o ¾ suma un poco, el perfil no resta | Vision |
| 10 | Cara completa | La caja de la cara no toca el borde del cuadro | Vision |
| 11 | Calidad de cara | `VNDetectFaceCaptureQualityRequest` (0–1) | Vision |

## C. Composición y estética (experimental, D7)
| # | Criterio | Cómo | Herramienta |
|---|---|---|---|
| 12 | Saliencia | El sujeto principal no queda cortado y cae en una zona agradable (tercios) | Vision saliencia |
| 13 | Estética | `VNCalculateImageAestheticsScoresRequest`; **solo se activa si gana en la prueba contra la elección del owner** | Vision (macOS 15+) |

## D. Para colorista
| # | Criterio | Cómo | Herramienta |
|---|---|---|---|
| 14 | Representativo del grade | Distancia del histograma del frame al histograma medio del plano (como el filtro `thumbnail` de ffmpeg) | numpy |
| 15 | Rango tonal | Que haya sombras, medios y altas (percentiles de luma) | numpy |
| 16 | Piel visible | Fracción de píxeles en la zona de tonos de piel (cerca de la skin line del vectorscopio) | numpy |

## E. Reglas de flujo
| # | Regla | Cómo |
|---|---|---|
| 17 | Los marcadores mandan | Los marcadores del color elegido dentro del clip son sus stills; ese plano no se analiza. AutoStills también los deja como salida (D20) |
| 18 | Diversidad con N stills | Uno por encuadre distinto (`select.framings`), hasta el máximo; de 0 a X por plano con descarte de planos cortos o blandos frente al resto del timeline (D19) |
| 19 | Clip repetido | El mismo media con un rango solapado dentro del timeline da un solo still |
| 20 | Saltar lo que no es plano | Se saltan títulos, generadores y compuestos sin media; los frames con mucho texto en pantalla se penalizan (Vision texto) |

## Presets (D6) — pesos por decidir
| Preset | Pesa más |
|---|---|
| Gallery de referencia | A, B, 15, 16 |
| Miniatura / redes | A, B, C |
| Contact sheet | A, 14 |

## Por decidir
- Pesos de cada preset y umbrales: con una prueba sobre timelines reales, el owner elige a mano y se compara (norma `prediccion-antes-de-medir.md`).
- Cuántos frames se muestrean por plano cuando no hay export válido (coste ~0,5 s/frame, H4). Con export se analizan todos (D17).
