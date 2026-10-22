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

## D3 — Repo público, licencia MIT — **pendiente del owner**
- **Contexto**: el resto de la familia es público y MIT.
- **Propuesta**: igual; sin publicar en GitHub hasta que el owner lo confirme.

## D4 — Nada del estudio entra en el repo
- **Elección**: ni nombre del estudio, ni clientes, ni rutas, ni IPs, ni material real (norma `repo-publico.md`, `make leak-check`).
- 2026-10-22, heredado de la familia.

## D5 — Git y versiones
- **Elección**: Conventional Commits en inglés con scope; SemVer desde `v0.1.0`; Keep a Changelog en español; sin trailers de atribución; nunca se commitea en `main` (rama + PR + CI verde) salvo el commit inicial del arranque.
- 2026-10-22, heredado de la familia.

## Pendientes del owner (entrevista de alcance)
Ver la bitácora 00: uso de los stills, criterios, número por plano, salida, plataforma, versiones de Resolve, camino para obtener frames y dependencias.
