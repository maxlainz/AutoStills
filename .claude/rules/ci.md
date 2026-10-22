# CI
*Norma de la familia de repos, adoptada aquí el 2026-10-22 (D2).*

- El gate es local: `make ci` = `leak-check` + `lint` (ruff, `select = ["E9","F"]`) + `test` (pytest, cuando haya código). Todo lo que corre en Actions es un target del Makefile, así local y CI están verdes o rojos a la vez.
- Actions corre en Linux (`.github/workflows/ci.yml`, `astral-sh/setup-uv`, Python 3.12) en push a `main` y en PRs.
- **La parte de Resolve no se puede probar en CI.** Lo que se prueba es la puntuación de frames sobre fixtures sintéticos.
- No se añaden ignores de ruff sin su `Dn`. Nunca se taggea con CI rojo.

**Por qué:** detectar regresiones en la puntuación antes de que el owner instale una versión rota en Resolve.
