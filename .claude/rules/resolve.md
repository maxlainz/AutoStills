# Resolve: cómo corre y cómo se prueba
*Norma provisional, 2026-10-22. Se cierra cuando el owner decida el stack (pendiente, ver `docs/decisiones.md`).*

- **El script se lanza desde Resolve** (Workspace › Scripts) y debe ser fácil de instalar: un instalador, sin pasos manuales en Terminal más allá de lanzarlo.
- **Detección de Resolve**: por los globales `resolve`/`bmd`. Lanzado desde Workspace › Scripts, `__name__` **no** es `"__main__"`; no se condiciona la GUI a `__main__`.
- **La GUI corre con el Python de Resolve: solo stdlib** a nivel de módulo. Si el análisis necesita librerías de terceros (numpy, OpenCV, modelos), corren en un worker aparte con su propio intérprete, nunca importadas en la GUI (lección de MHL MediaManagement: un import de terceros rompe el script en el menú de Resolve sin error visible).
- **El análisis se prueba sin Resolve**: la lógica de puntuación recibe imágenes y devuelve puntuaciones, y es lo que cubren `make test` y la CI. La parte que habla con Resolve solo se prueba dentro de Resolve (a mano o con el MCP de Resolve).
- **Nunca se modifica el proyecto del owner sin avisar**: ni gradings, ni timeline, ni cambios de página, salvo lo que el flujo pida explícitamente (crear stills en un álbum).
- **Zombis**: los procesos `fuscript` hijos de Resolve que mueren quedan zombis hasta reiniciar Resolve. No se diagnostica un cuelgue sin mirarlo primero.

**Por qué:** que se instale y se lance sin fricción es un requisito del owner, y la GUI de Resolve no se puede probar en CI.
