#!/bin/sh
# Builds dist/parley-tray_<version>_all.deb and a source tarball from this checkout.
set -eu
umask 022
root=$(cd "$(dirname "$0")" && pwd)
version=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$root/parley_tray/__init__.py")
dist="$root/dist"
pkg="$dist/pkg"
rm -rf "$pkg"
mkdir -p "$pkg/DEBIAN" "$pkg/usr/lib/parley-tray/bin" "$pkg/usr/bin" "$pkg/usr/share/applications" \
  "$pkg/etc/xdg/autostart" "$pkg/usr/share/icons/hicolor/scalable/apps" "$pkg/usr/share/doc/parley-tray"

cp -r "$root/parley_tray" "$root/data" "$pkg/usr/lib/parley-tray/"
chmod -R go-w "$pkg/usr/lib/parley-tray"
find "$pkg" -name __pycache__ -prune -exec rm -rf {} +
cp "$root/bin/parley-tray" "$pkg/usr/lib/parley-tray/bin/"
ln -s ../lib/parley-tray/bin/parley-tray "$pkg/usr/bin/parley-tray"
cp "$root/data/icons/parley-tray.svg" "$pkg/usr/share/icons/hicolor/scalable/apps/io.github.tuzkituan.ParleyTray.svg"
for f in parley-tray.desktop parley-tray-autostart.desktop; do
  sed -e "s|@BIN@|parley-tray|" -e "s|@ICON@|io.github.tuzkituan.ParleyTray|" "$root/data/$f.in" > "$pkg/$f"
done
mv "$pkg/parley-tray.desktop" "$pkg/usr/share/applications/io.github.tuzkituan.ParleyTray.desktop"
mv "$pkg/parley-tray-autostart.desktop" "$pkg/etc/xdg/autostart/parley-tray.desktop"
cp "$root/README.md" "$root/LICENSE" "$pkg/usr/share/doc/parley-tray/"

cat > "$pkg/DEBIAN/control" <<CONTROL
Package: parley-tray
Version: $version
Architecture: all
Maintainer: Tuan Nguyen <tuannguyenitpy@gmail.com>
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1 (>= 1.7), gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, gir1.2-secret-1
Recommends: gnome-shell-extension-appindicator
Section: utils
Priority: optional
Homepage: https://github.com/tuzkituan/parley-tray
Description: Translate text or fix your English from the GNOME top bar
 A tray icon and Super+T / Super+G shortcuts that open a small window with the
 selected text translated (Google Translate) or proofread (LanguageTool or Gemini).
CONTROL

dpkg-deb --root-owner-group --build "$pkg" "$dist/parley-tray_${version}_all.deb" >/dev/null
rm -rf "$pkg"
git -C "$root" archive --format=tar.gz --prefix="parley-tray-$version/" -o "$dist/parley-tray-$version.tar.gz" HEAD
ls "$dist"
