# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado: [SemVer](https://semver.org/lang/es/). Categorías: Añadido · Cambiado · Corregido · Decidido · Medido · Eliminado.

## [Unreleased]
### Añadido
- Arranque del repo con el método de la familia: normas, hooks, skills, `make ci`, CI, `leak-check` (bitácora 00).
- Investigación de opciones: API de Resolve 21.1, caminos para obtener frames, señales de puntuación, precedentes (`docs/investigacion.md`).

### Añadido (GitHub)
- `main` protegida, secret scanning, alertas de vulnerabilidades y Dependabot (D12).

### Medido
- H1: la miniatura de la Color page es fija por clip y de 576×324. H2: `ExportCurrentFrameAsStill` da el frame graduado a resolución de timeline en ~0,5 s, sin frames atrasados (bitácora 01).

### Decidido
- D1 (nombre AutoStills), D2 (método de la familia), D3 (público, MIT), D4 (nada del estudio en el repo), D5 (git y versiones).
- Entrevista de alcance: D6 (varios usos con presets), D7 (nitidez, caras y ojos, exposición; estética experimental), D8 (álbum nuevo de la Gallery), D9 (solo Mac + Resolve Studio 21.1+), D10 (1 still por plano, ajustable), D11 (instalador de un paso con uv), D12 (protección de `main` y seguridad del repo), D13 (frames con `ExportCurrentFrameAsStill`).
