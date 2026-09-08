#!/usr/bin/env bash
# Install the AbletonMCPUnified Remote Script into Live's User Library.
#   scripts/install_remote_script.sh            # symlink (default, stays in sync with the repo)
#   scripts/install_remote_script.sh --copy     # copy instead
#   scripts/install_remote_script.sh --force    # replace an existing real directory
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$HERE/AbletonMCPUnified"
DEST_DIR="${ABLETON_REMOTE_SCRIPTS_DIR:-$HOME/Music/Ableton/User Library/Remote Scripts}"
DEST="$DEST_DIR/AbletonMCPUnified"
MODE=symlink; FORCE=0
for arg in "$@"; do
  case "$arg" in
    --copy) MODE=copy ;;
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done
mkdir -p "$DEST_DIR"
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  if [ -L "$DEST" ]; then
    rm "$DEST"
  elif [ "$FORCE" = 1 ]; then
    rm -rf "$DEST"
  else
    echo "Refusing to replace existing non-symlink $DEST (use --force)" >&2; exit 1
  fi
fi
find "$SRC" -name __pycache__ -type d -prune -exec rm -rf {} +
if [ "$MODE" = symlink ]; then
  ln -s "$SRC" "$DEST"; echo "Symlinked $DEST -> $SRC"
else
  cp -R "$SRC" "$DEST"; echo "Copied $SRC -> $DEST"
fi
if [ -d "$DEST_DIR/AbletonMCP" ]; then
  echo "NOTE: the old AbletonMCP Remote Script is still installed and also binds port 9877."
  echo "      Enable only ONE of them as a Control Surface in Live, or the second will fail to bind."
fi
cat <<MSG

Next steps in Ableton Live:
  1. Restart Live (or re-scan): Live > Settings > Link, Tempo & MIDI.
  2. In a Control Surface slot choose "AbletonMCPUnified" (Input/Output: None).
  3. Verify with the MCP tool health_check -> rs_version "unified-…".
MSG
