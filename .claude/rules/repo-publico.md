# Repo público: nada del estudio entra en el repo
*Norma de la familia de repos, adoptada aquí el 2026-10-22 (D4). El repo es público (D3).*

- Nunca se versionan: el nombre del estudio, nombres de clientes, campañas o productoras; rutas reales, IPs, nombres de host o shares; credenciales; material de proyectos (vídeo, stills reales, LUTs, `.drp`, `.dra`, `.drx`).
- **El nombre del estudio solo vive en `scripts/leak-patterns.local.txt`** (gitignored), que `scripts/leak-check.sh` lee como patrón prohibido.
- **El único volumen de ejemplo es el marcador `/Volumes/X`.** Cualquier otro `/Volumes/<algo>` en un fichero versionado es un fallo de `make leak-check` y lo bloquea el hook `PostToolUse`.
- Los fixtures de test (frames con caras, desenfoque, sobreexposición) se generan sintéticamente o salen de bancos con licencia que permita redistribuirlos, citada junto al fixture. Nunca frames de un trabajo real.
- Antes de cada push: `make leak-check` (va dentro de `make ci`).

**Por qué:** lo que entra en el historial de git no sale.
