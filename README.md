# AutoStills

Script para **DaVinci Resolve Studio** que saca automáticamente el **mejor still de cada plano** del timeline: no el primer frame ni el del medio, sino el más nítido, con menos desenfoque de movimiento, bien expuesto y, si hay gente, con la cara bien vista.

**TL;DR.** Estado: **arranque, sin código**. Investigación en `docs/investigacion.md`, decisiones en `docs/decisiones.md`, plan en `docs/roadmap.md`. Para trabajar en el repo: `CLAUDE.md`.

Se lanzará desde Resolve: **Workspace › Scripts › AutoStills**.

## Idea
1. Lee los planos del timeline.
2. Muestrea frames de cada plano, graduados por el propio Resolve (sirve cualquier códec, también RAW).
3. Puntúa cada frame: nitidez, movimiento, exposición, caras.
4. Mueve el cabezal al ganador de cada plano y hace *Grab Still* en un álbum nuevo de la Gallery.

## Instalación
Pendiente. Requisito de diseño: un solo paso, sin Terminal.

## Desarrollo
`make setup` (dependencias en `.venv` con `uv`) · `make ci` (leak-check + ruff + tests; lo mismo que corre GitHub Actions).

## Cómo se trabaja
El método (router, normas, decisiones, bitácora) está en `CLAUDE.md` y `.claude/rules/`.

## Licencia
MIT. Ver `LICENSE`.
