# Pull al abrir, push al cerrar
*Norma de la familia de repos, adoptada aquí el 2026-10-22 (D2).*

- Al abrir sesión: `git fetch --prune` y `git pull --ff-only` si el árbol está limpio (hook `SessionStart`).
- Al cerrar sesión y tras cada tarea commiteada: `git push` de la rama actual (hook `Stop`).
- Si `main` ha divergido: `git cherry origin/main main`; si no hay líneas `+`, `git reset --hard origin/main`; si las hay, preguntar al owner.
- Ramas de trabajo se rebasan sobre `origin/main` antes de abrir el PR. `main` nunca recibe commits locales (D5): si la sesión arranca en `main`, la primera acción de una tarea es crear la rama.
- Sin remoto configurado (antes de publicar el repo) los hooks no hacen nada.

**Por qué:** el owner trabaja desde varias máquinas; un push olvidado es trabajo perdido.
