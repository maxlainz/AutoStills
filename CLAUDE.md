# AutoStills

Script para **DaVinci Resolve Studio** que elige y captura automáticamente el mejor still de cada plano del timeline (nitidez, poco desenfoque de movimiento, exposición, caras) en vez del primer frame o el central. Corre desde Workspace › Scripts y debe ser fácil de entender e instalar.

**Este archivo es el router: lo único que un agente necesita leer para arrancar.** Sin conocimiento de dominio aquí; todo vive en el archivo al que apunta. Se actualiza en cada commit que cambie estructura, estado o comandos.

## Mapa del repo
```
CLAUDE.md              este router
.claude/rules/         normas (una por archivo)        .claude/skills/   release · obsidian-vault
.claude/settings.json  hooks: pull + issues al arrancar · bloqueo de rutas al escribir · bloqueo de commit en main · push al cerrar
docs/decisiones.md     ADRs D1–D24                      docs/bitacora/    una entrada por sesión (00 arranque · 01 medida · 02 worker · 03 prueba en Resolve · 04 v0.1.0)
docs/investigacion.md  API de Resolve, caminos para obtener frames, señales, precedentes, stack candidato, JEV
docs/criterios.md      los 20 criterios de selección, cómo medirlos y presets
docs/roadmap.md        versiones previstas
AutoStills.py          la ventana dentro de Resolve (solo stdlib): planos, fuente, comprobación, muestreo, Grab Still
autostills/            worker de puntuación (fuera de Resolve): metrics · select · faces (Apple Vision) · worker (CLI)
install.command        instalador de un doble clic: uv + entorno en ~/Library/Application Support/AutoStills (D11)
tests/                 pytest sobre frames sintéticos  samples/          material local del owner (gitignored)
.github/               ci.yml (push a main y PRs) · dependabot.yml pyproject.toml · .python-version
scripts/leak-check.sh  nada del estudio en el repo     scripts/leak-patterns.local.txt  patrones privados (gitignored)
Makefile · CHANGELOG.md · README.md · LICENSE (MIT)
```

## Normas (`.claude/rules/`)
| Archivo | Qué manda |
|---|---|
| `entrevista.md` | Preguntar al owner antes de suponer; las propuestas también; recomendación primero; bocetos en texto para la GUI |
| `repo-publico.md` | Nada del estudio ni material real en el repo; fixtures sintéticos o con licencia; `make leak-check` (D4) |
| `resolve.md` | GUI solo stdlib (D9, D11); análisis en worker aparte; no tocar el proyecto del owner sin avisar |
| `decisiones-y-bitacora.md` | ADR por decisión, bitácora por sesión, `Hn` citados desde el código, `CLAUDE.md` y `CHANGELOG` al día |
| `prediccion-antes-de-medir.md` | Predicción escrita antes de cada medida (s/plano, coste de leer un frame desde Resolve) |
| `subagentes.md` | Orquestar y delegar; Opus para research/diseño/revisión, Sonnet para implementación, Haiku para inventarios |
| `git.md` | Nunca en `main`: rama + PR + CI verde, `main` protegida en GitHub (D12); Conventional Commits, SemVer, Keep a Changelog, sin trailers (D5) |
| `pull-y-push.md` | Pull al abrir, push al cerrar |
| `issues-abiertos.md` | Leer `gh issue list` antes de cualquier tarea |
| `problemas-al-issue.md` | Lo que se encuentra y no se arregla, a issue |
| `sin-rutas-absolutas.md` | Sin `/Users/...`, shares ni IPs; hook que bloquea |
| `ci.md` | Gate local `make ci` (leak-check + lint + test); Actions en Linux |
| `obsidian.md` | El vault es la base de conocimiento; área y nota de proyecto pendientes del owner |
| `vault-accesible.md` | Sin vault que responda no arranca una tarea de dominio; lotes de 3–6 lecturas |

## Docs
| Archivo | Leer cuando… |
|---|---|
| `docs/investigacion.md` | Antes de elegir cómo obtener frames, qué señales puntuar o qué dependencia añadir |
| `docs/criterios.md` | Vas a tocar la puntuación de frames, los presets o las reglas de flujo (código en `autostills/select.py`) |
| `docs/decisiones.md` | Antes de tocar alcance, nombres, herramientas o workflow |
| `docs/roadmap.md` | Dudas de qué entra en cada versión |
| `docs/bitacora/` | Quieres saber qué pasó en cada sesión |

## Comandos
```sh
make setup   # uv sync: .venv con numpy, OpenCV, pyobjc-Vision, pytest y ruff
uv run python -m autostills.worker job.json result.json   # contrato del job en el docstring de autostills/worker.py
make install-link   # instala en Resolve con enlaces al repo (desarrollo); make install para copiar
make ci      # leak-check + lint + test — el gate de cada commit
```

## Estado y siguiente paso
- **Estado (2026-10-22, bitácora 04)**: **v0.1.0 publicada** y aprobada por el owner tras probarla en Resolve. Incluye la ventana v2 (D18–D24), el worker con dos pasadas y encuadres por movimiento de cámara (H11), el último export como fuente (D17, H6–H8) y Grab Still robusto (H13, H14). 39 tests.
- **Después**: prueba de pesos con los marcadores del owner (los umbrales y los pesos son a ojo); calibrar el umbral de la comprobación del export; explorar JEV sobre la preselección (D16).

## Pendiente del owner (2026-10-22)
- Área del vault y nota de proyecto `AutoStills` (sin decidir, así que las notas de concepto de esta versión siguen pendientes).
- Borrar a mano el álbum vacío «AutoStills diagnóstico (se puede borrar)» de la Gallery de BarraDunBar.
- Crear `scripts/leak-patterns.local.txt` con el nombre del estudio y de clientes.
