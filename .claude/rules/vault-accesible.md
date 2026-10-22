# Sin vault accesible no se arranca una tarea de dominio
*Norma de la familia de repos (MHL Sentinel), adoptada aquí el 2026-10-22 (D2).*

- Antes de arrancar una tarea con contenido de dominio (métricas de nitidez, detección facial, puntuación estética, color de los stills) se **comprueba que el vault responde** (`obsidian_list_vaults`) y se leen las notas que esa tarea necesita (lista en `CLAUDE.md`). Si no responde: **se para y se avisa al owner**.
- Lotes de 3–6 lecturas, nunca más.

**Por qué:** en otro repo de la familia un trabajo entero arrancó sin leer las notas de concepto porque el servidor se había caído, y la auditoría posterior encontró diez hallazgos concentrados exactamente ahí.
