# AutoStills

Script para **DaVinci Resolve Studio** que saca automáticamente el **mejor still de cada plano** del timeline: no el primer frame ni el del medio, sino el más nítido, con menos desenfoque de movimiento, bien expuesto y, si hay gente, con la cara bien vista.

**TL;DR.** Estado: **primera versión para probar, sin tag**. Investigación en `docs/investigacion.md`, decisiones en `docs/decisiones.md`, plan en `docs/roadmap.md`. Para trabajar en el repo: `CLAUDE.md`.

Se lanzará desde Resolve: **Workspace › Scripts › AutoStills**.

## Cómo funciona
1. Lee los planos del timeline en las pistas elegidas. La pista de encima tapa a la de abajo. Se saltan títulos y generadores, y un clip repetido no da otro still.
2. **Fuente** (D17):
   - **Último export del timeline (mejor).** Analiza *todos* los frames del render más reciente de la cola de render. Antes comprueba, plano a plano, que el render cuadra con lo que Resolve muestra ahora; los planos que no cuadran se analizan por muestreo.
   - **Desde el timeline (muestreo).** Lee 12 frames graduados por plano desde Resolve (~0,5 s por frame).
3. Puntúa cada frame (`docs/criterios.md`): nitidez, movimiento, exposición, foco, caras (ojos, boca, orientación, cara completa), composición, texto en pantalla, representatividad, rango tonal y piel.
4. Mueve el cabezal al frame ganador de cada plano y hace *Grab Still* en un álbum nuevo de la Gallery, con la etiqueta «CLIP · TC». Si un clip tiene un marcador del color elegido, se usa ese frame.

Al terminar, el cabezal y la página vuelven a donde estaban, y los frames temporales se borran.

## Instalación
1. Descarga el repo y haz **doble clic en `install.command`**. La primera vez macOS puede bloquearlo: clic derecho › Abrir.
2. Instala `uv` si no está y crea en `~/Library/Application Support/AutoStills/` un entorno propio (~180 MB) con numpy, OpenCV y Apple Vision. No toca el Python del sistema ni el de Resolve.
3. En Resolve Studio 21.1 o posterior: **Workspace › Scripts › AutoStills**.

Requisitos: macOS con Apple Silicon y DaVinci Resolve Studio ≥ 21.1 (D9). Para desinstalar, borra `~/Library/Application Support/AutoStills/` y `AutoStills.py` de `…/Fusion/Scripts/Utility/`.

## Desarrollo
`make setup` (dependencias en `.venv` con `uv`) · `make ci` (leak-check + ruff + tests; lo mismo que corre GitHub Actions) · `make install-link` (instala con enlaces al repo). El worker se puede usar sin Resolve: `uv run python -m autostills.worker job.json result.json` (contrato en `autostills/worker.py`).

## Cómo se trabaja
El método (router, normas, decisiones, bitácora) está en `CLAUDE.md` y `.claude/rules/`.

## Licencia
MIT. Ver `LICENSE`.
