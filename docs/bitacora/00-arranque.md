# 00 — Arranque (2026-10-22)

**TL;DR.** Repo nuevo con el método de la familia (plantilla: MHL MediaManagement) e investigación de opciones en `docs/investigacion.md`. No hay código. Falta la entrevista de alcance: las preguntas abiertas están abajo y se registrarán como `Dn`.

## Qué se leyó
- Los repos hermanos del owner, en especial **MHL MediaManagement** (script de Resolve: router, normas, hooks, skills, CI, `leak-check`).
- La API de scripting de Resolve 21.1 y el changelog 19→21.1 (MCP de Resolve).
- Research delegado en un subagente: métricas de nitidez y movimiento, detección facial, modelos estéticos, precedentes (Yahoo Hecate) y el problema de decodificar RAW.

## Qué se hizo
- `git init`, `LICENSE` (MIT), `.gitignore`, `Makefile`, `pyproject.toml`, `.python-version`, `scripts/leak-check.sh`, `.claude/` (normas, hooks, skills `release` y `obsidian-vault`), `.github/workflows/ci.yml`, `docs/` (decisiones D1–D5, investigación, roadmap provisional, esta bitácora), `README.md`, `CHANGELOG.md`, `CLAUDE.md`.
- Normas adaptadas: `resolve.md` (nueva, provisional), `entrevista.md` (las propuestas también se preguntan), `repo-publico.md` (fixtures), `obsidian.md` (área pendiente).
- Sin remoto: no se ha publicado en GitHub (D3 pendiente).

## Hallazgos de la investigación (sin medir)
- Resolve 21.1 trae Python 3.14 propio sin `pip` y los scripts Python pasan a ser solo de Studio.
- `GetCurrentClipThumbnailImage` podría darnos los frames graduados sin render ni decodificar fuera: hay que medir resolución y velocidad.
- ffmpeg/OpenCV no decodifican BRAW, R3D ni ARRIRAW → que decodifique Resolve.
- Apple Vision (pyobjc, MIT) da caras, calidad de cara, landmarks, saliencia y puntuación estética sin descargar modelos, solo en macOS.

## Siguiente paso
1. Entrevista de alcance con el owner → `Dn`.
2. Medir el camino A (miniaturas) en un timeline real, con predicción previa.
3. Publicar en GitHub si el owner confirma D3.
