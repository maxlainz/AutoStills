# Entrevistar al owner antes de suponer
*Norma de la familia de repos, adoptada aquí el 2026-10-22 (D2). El owner la marcó como «importantísima» en el arranque.*

- Toda decisión de producto, alcance, UX, criterios de puntuación de un still o workflow se pregunta antes de implementarla. Preguntas concretas, con recomendación primero y trade-offs después.
- Las preguntas se hacen con `AskUserQuestion` cuando la sesión es interactiva; si no lo es, van en el mensaje final agrupadas y numeradas. Una pregunta enterrada en prosa cuenta como no hecha.
- Las propuestas (algoritmos nuevos, cambios de alcance, dependencias) también se presentan como pregunta antes de implementarlas.
- Las respuestas se registran el mismo día en `docs/decisiones.md` como `Dn`. Una decisión cerrada no se vuelve a preguntar.
- El owner es colorista, no ingeniero: español, TL;DR primero, jerga explicada la primera vez, analogías con Resolve (Gallery, Color page, Grab Still) cuando ayuden.
- Cualquier cambio en la ventana de Resolve (botones, textos, pasos del flujo) se enseña primero como boceto en texto plano.

**Por qué:** el coste de preguntar es un mensaje; el de suponer mal es rehacer el trabajo.
