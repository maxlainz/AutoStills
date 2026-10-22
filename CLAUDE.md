# AutoStills

Script para **DaVinci Resolve Studio** que elige y captura automáticamente el mejor still de cada plano del timeline (nitidez, poco desenfoque de movimiento, exposición, caras) en vez del primer frame o el central. Corre desde Workspace › Scripts y debe ser fácil de entender e instalar.

**Este archivo es el router: lo único que un agente necesita leer para arrancar.** Sin conocimiento de dominio aquí; todo vive en el archivo al que apunta. Se actualiza en cada commit que cambie estructura, estado o comandos.

## Mapa del repo
```
CLAUDE.md              este router
.claude/rules/         normas (una por archivo)        .claude/skills/   release · obsidian-vault
.claude/settings.json  hooks: pull + issues al arrancar · bloqueo de rutas al escribir · bloqueo de commit en main · push al cerrar
docs/decisiones.md     ADRs D1–Dn                      docs/bitacora/    una entrada por sesión (00 arranque)
docs/investigacion.md  API de Resolve, caminos para obtener frames, señales, precedentes, stack candidato
docs/roadmap.md        versiones previstas (provisional)
tests/                 vacío hasta que haya código     samples/          material local del owner (gitignored)
.github/workflows/     ci.yml (push a main y PRs)      pyproject.toml · .python-version
scripts/leak-check.sh  nada del estudio en el repo     scripts/leak-patterns.local.txt  patrones privados (gitignored)
Makefile · CHANGELOG.md · README.md · LICENSE (MIT)
```

## Normas (`.claude/rules/`)
| Archivo | Qué manda |
|---|---|
| `entrevista.md` | Preguntar al owner antes de suponer; las propuestas también; recomendación primero; bocetos en texto para la GUI |
| `repo-publico.md` | Nada del estudio ni material real en el repo; fixtures sintéticos o con licencia; `make leak-check` (D4) |
| `resolve.md` | (provisional) GUI solo stdlib; análisis en worker aparte; no tocar el proyecto del owner sin avisar |
| `decisiones-y-bitacora.md` | ADR por decisión, bitácora por sesión, `Hn` citados desde el código, `CLAUDE.md` y `CHANGELOG` al día |
| `prediccion-antes-de-medir.md` | Predicción escrita antes de cada medida (s/plano, coste de leer un frame desde Resolve) |
| `subagentes.md` | Orquestar y delegar; Opus para research/diseño/revisión, Sonnet para implementación, Haiku para inventarios |
| `git.md` | Nunca en `main`: rama + PR + CI verde; Conventional Commits, SemVer, Keep a Changelog, sin trailers (D5) |
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
| `docs/decisiones.md` | Antes de tocar alcance, nombres, herramientas o workflow |
| `docs/roadmap.md` | Dudas de qué entra en cada versión |
| `docs/bitacora/` | Quieres saber qué pasó en cada sesión |

## Comandos
```sh
make setup   # uv sync: .venv con pytest y ruff
make ci      # leak-check + lint + test — el gate de cada commit
```

## Estado y siguiente paso
- **Estado (2026-10-22, bitácora 00)**: repo creado en local con el método de la familia; investigación hecha; sin código; sin remoto.
- **Después**: entrevista de alcance → medir el camino «miniaturas de la Color page» → v0.1.0.

## Pendiente del owner (2026-10-22)
- Entrevista de alcance (preguntas en la bitácora 00 y en el chat).
- D3: ¿repo público en GitHub con MIT?
- Área del vault y nota de proyecto `AutoStills`.
- Crear `scripts/leak-patterns.local.txt` con el nombre del estudio y de clientes.
