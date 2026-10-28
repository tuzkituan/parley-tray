#!/bin/sh
# Installs Parley Tray from this checkout for the current user: launcher, app menu entry,
# autostart. Super+T / Super+G are set up on first run. ./install.sh --uninstall removes it all.
# Run again after moving the checkout.
set -eu
root=$(cd "$(dirname "$0")" && pwd)
bin="$HOME/.local/bin/parley-tray"
apps="$HOME/.local/share/applications/io.github.tuzkituan.ParleyTray.desktop"
autostart="$HOME/.config/autostart/parley-tray.desktop"

if [ "${1:-}" = --uninstall ]; then
  "$bin" --quit 2>/dev/null || true
  "$bin" --remove-shortcuts 2>/dev/null || true
  rm -f "$bin" "$apps" "$autostart"
  echo "Removed Parley Tray."
  exit 0
fi

mkdir -p "$(dirname "$bin")" "$(dirname "$apps")" "$(dirname "$autostart")"
ln -sf "$root/bin/parley-tray" "$bin"
icon="$root/data/icons/parley-tray.svg"
sed -e "s|@BIN@|$bin|" -e "s|@ICON@|$icon|" "$root/data/parley-tray.desktop.in" > "$apps"
sed -e "s|@BIN@|$bin|" -e "s|@ICON@|$icon|" "$root/data/parley-tray-autostart.desktop.in" > "$autostart"
echo "Installed $bin"
"$bin" --background &
echo "Parley Tray is running."
