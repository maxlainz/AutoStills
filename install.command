#!/bin/bash
# AutoStills — instalador (D11). Doble clic en Finder (la primera vez: clic derecho › Abrir).
#   ./install.command          copia el script a Resolve y crea el entorno del análisis
#   ./install.command --link   enlaces al repo en vez de copias (desarrollo)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$HOME/Library/Application Support/AutoStills"
SCRIPTS="$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility"
echo "AutoStills — instalando…"
UV="$(command -v uv || true)"
[ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ] && UV="$HOME/.local/bin/uv"
if [ -z "$UV" ]; then
  echo "Instalando uv (crea el Python del análisis sin tocar el del sistema ni el de Resolve)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  UV="$HOME/.local/bin/uv"
fi
mkdir -p "$APP" "$SCRIPTS"
rm -rf "$APP/app" "$SCRIPTS/AutoStills.py"
if [ "$1" = "--link" ]; then
  ln -s "$DIR" "$APP/app"
  ln -s "$DIR/AutoStills.py" "$SCRIPTS/AutoStills.py"
else
  mkdir -p "$APP/app"
  cp -R "$DIR/autostills" "$DIR/pyproject.toml" "$DIR/uv.lock" "$DIR/.python-version" "$APP/app/"
  cp "$DIR/AutoStills.py" "$SCRIPTS/AutoStills.py"
fi
(cd "$APP/app" && UV_PROJECT_ENVIRONMENT="$APP/.venv" "$UV" sync --frozen --no-dev --quiet)
(cd "$APP/app" && "$APP/.venv/bin/python" -c \
  "from autostills import faces; print('✓ Apple Vision', 'disponible' if faces.available() else 'NO disponible (caras desactivadas)')")
echo "✓ Listo. En Resolve Studio: Workspace › Scripts › AutoStills (reinicia Resolve si no aparece)."
[ -t 0 ] && read -n 1 -s -r -p "Pulsa una tecla para cerrar." || true
