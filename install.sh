#!/bin/sh
# Installs Parley Tray for the current user: launcher, app menu entry, autostart, shortcuts.
# Run again after moving the checkout. ./install.sh --uninstall removes it all.
set -eu
root=$(cd "$(dirname "$0")" && pwd)
bin="$HOME/.local/bin/parley-tray"
apps="$HOME/.local/share/applications/io.github.tuzkituan.ParleyTray.desktop"
autostart="$HOME/.config/autostart/parley-tray.desktop"
keys=org.gnome.settings-daemon.plugins.media-keys
base=/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings

list() { gsettings get $keys custom-keybindings | sed 's/^@as //'; }

remove_shortcut() {
  path="$base/$1/"
  new=$(list | python3 -c "import ast,sys; l=ast.literal_eval(sys.stdin.read()); print([p for p in l if p != '$path'])")
  gsettings set $keys custom-keybindings "$new"
  gsettings reset-recursively "$keys.custom-keybinding:$path"
}

add_shortcut() { # id name binding command
  path="$base/$1/"
  taken=$(for p in $(list | tr -d "[],'"); do
    [ "$p" = "$path" ] && continue
    gsettings get "$keys.custom-keybinding:$p" binding
  done; gsettings list-recursively org.gnome.desktop.wm.keybindings; gsettings list-recursively org.gnome.shell.keybindings)
  if printf '%s' "$taken" | grep -qiF "'$3'"; then
    echo "  skipped $3 ($2): already used; set one in Settings > Keyboard > Custom Shortcuts"
    return
  fi
  new=$(list | python3 -c "import ast,sys; l=ast.literal_eval(sys.stdin.read()); print(l if '$path' in l else l+['$path'])")
  gsettings set $keys custom-keybindings "$new"
  gsettings set "$keys.custom-keybinding:$path" name "$2"
  gsettings set "$keys.custom-keybinding:$path" binding "$3"
  gsettings set "$keys.custom-keybinding:$path" command "$4"
  echo "  $3: $2"
}

if [ "${1:-}" = --uninstall ]; then
  "$bin" --quit 2>/dev/null || true
  rm -f "$bin" "$apps" "$autostart"
  remove_shortcut parley-translate
  remove_shortcut parley-fix
  echo "Removed Parley Tray."
  exit 0
fi

mkdir -p "$(dirname "$bin")" "$(dirname "$apps")" "$(dirname "$autostart")"
ln -sf "$root/bin/parley-tray" "$bin"
icon="$root/data/icons/parley-tray-symbolic.svg"
sed -e "s|@BIN@|$bin|" -e "s|@ICON@|$icon|" "$root/data/parley-tray.desktop.in" > "$apps"
sed -e "s|@BIN@|$bin|" -e "s|@ICON@|$icon|" "$root/data/parley-tray-autostart.desktop.in" > "$autostart"
echo "Installed $bin"
echo "Shortcuts:"
add_shortcut parley-translate "Parley: Translate" "<Super>t" "$bin --translate"
add_shortcut parley-fix "Parley: Fix English" "<Super>g" "$bin --fix"
"$bin" --background &
echo "Parley Tray is running."
