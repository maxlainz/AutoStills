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

## D10 — Stills por plano: 1 por defecto, ajustable
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

## Pendientes
- **Cómo obtener los frames** (miniaturas de la Color page vs proxy renderizado): se decide midiendo. El owner pospuso la medida en su proyecto abierto porque estaba renderizando (2026-10-22).
- Presets concretos y sus pesos (D6), boceto de la ventana.
