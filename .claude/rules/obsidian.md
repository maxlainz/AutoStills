# Obsidian es la base de conocimiento
*Norma de la familia de repos, adoptada aquí el 2026-10-22 (D2). El contrato del vault es la nota `Claude` y manda sobre esta norma.*

- **El vault no es documentación de este proyecto.** Estado, decisiones, hallazgos, bitácora y plan viven aquí. En el vault habrá **una sola** nota de proyecto, `AutoStills`, estilo readme: qué es, dónde vive la documentación y los conceptos en los que se apoya. Se actualiza cuando cambia lo que es o los conceptos que usa; nunca con estado.
- **La nota `AutoStills` y su área aún no existen; crearlas y elegir el área es decisión pendiente del owner.** Hasta que lo autorice, no se crean.
- Se **referencian notas por título** en docs, issues, commits y comentarios de código. Las notas de concepto son la fuente; el repo no las copia, las cita.
- **Investigar obliga a documentar, y es condición de cierre de sesión**: todo concepto nuevo (p. ej. varianza del laplaciano, detección facial, puntuación estética) se escribe como nota `#concepto` (o se amplía la existente) antes de cerrar la sesión, una vez el owner haya decidido el área. Ante la duda de si es concepto, sistema o proyecto, qué nombre o qué área, se pregunta al owner.
- Formato de una nota de concepto: definición en una frase + «Relacionado: [[…]]» · **Definición** · **Propiedades** (opcional) · **Fórmulas o medida** (opcional) · **Limitaciones** · **Fuentes**. Prohibido dentro: identificadores `Dn`/`Hn`, rutas del repo, cifras atribuidas al proyecto, «el script hace…».
- **No se borra ni se funde una nota sin permiso.**
- Mecánica del MCP (id `my-vault`, vault plano, nota `X` en `X.md`): buscar con `obsidian_search_vault`; **máximo 3–6 lecturas por lote**; editar solo con el `etag` de una lectura fresca. Si el servidor se cae, parar y avisar al owner.

**Por qué:** los conceptos se reutilizan entre repos de la familia en vez de duplicarse en `docs/`.
