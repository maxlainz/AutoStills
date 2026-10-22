# 00 — Arranque (2026-10-22)

**TL;DR.** Repo nuevo con el método de la familia (plantilla: MHL MediaManagement) e investigación de opciones en `docs/investigacion.md`. No hay código. Entrevista de alcance en dos rondas → D3, D6–D11. Publicado en GitHub.

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

## Entrevista de alcance
1. **¿Uso?** → varios: Gallery de referencia, miniaturas/redes y contact sheet, con presets. D6.
2. **¿Criterios?** → nitidez/motion blur, caras con ojos abiertos, exposición y estética; «la estética hay que testearla». D7.
3. **¿Salida?** → álbum nuevo de la Gallery. D8.
4. **¿Plataforma?** → solo Mac + Resolve Studio 21.1+. D9.
5. **¿Stills por plano?** → 1 por defecto, ajustable. D10.
6. **¿Medir en el proyecto abierto?** → todavía no: estaba renderizando.
7. **¿Instalación?** → un paso con uv. D11.
8. **¿GitHub?** → público, MIT. D3.

## Siguiente paso
1. Medir el camino A (miniaturas de la Color page) con predicción previa, cuando el owner lo permita.
2. Boceto de la ventana y de los presets (D6) para que el owner lo apruebe.
3. v0.1.0.
