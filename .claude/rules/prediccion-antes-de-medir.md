# Predicción antes de medir
*Norma de la familia de repos, adoptada aquí el 2026-10-22 (D2).*

- Antes de cada medida se escribe la predicción: orden de magnitud y criterio de éxito. Medidas típicas: segundos por clip analizado; frames muestreados por segundo; coste de mover el cabezal y leer un frame desde Resolve; acierto del still elegido frente al que elegiría el owner.
- Una predicción fallida se registra como hallazgo `Hn` en la bitácora, con el comando que la reproduce.

**Por qué:** sin predicción, un análisis que tarda diez minutos por timeline pasa por «normal».
