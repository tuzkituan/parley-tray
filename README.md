# Parley Tray

Translate text or fix your English from the GNOME top bar. The desktop sibling of the [Parley](https://github.com/tuzkituan/parley) browser extension.

| To | Do |
| --- | --- |
| Fix the English of the selected text | **Super+G**, or Fix English in the tray menu |
| Translate the selected text | **Super+T**, or Translate in the tray menu |
| Run again now | **Ctrl+Enter** |
| Copy the result and close | **Ctrl+Shift+C** |
| Close | **Esc** |

The window opens with the selected text (or the clipboard) already filled in and done. Translation goes into your language, or into English when the text is already in your language. In Fix English, changed words are underlined.

## Install

Needs GNOME 45+ with the AppIndicator extension (on by default in Ubuntu) and libadwaita 1.7+ (Ubuntu 25.04 or newer).

Download `parley-tray_<version>_all.deb` from the [latest release](https://github.com/tuzkituan/parley-tray/releases/latest), then:

```sh
sudo apt install ./parley-tray_*_all.deb
parley-tray
```

It starts at login from then on. The first run sets up **Super+T** and **Super+G**, skipping any key that's already taken; change them in Settings > Keyboard > Custom Shortcuts (commands `parley-tray --translate` and `parley-tray --fix`). `parley-tray --remove-shortcuts` takes them out.

### From a checkout

```sh
sudo apt install python3-gi gir1.2-adw-1 gir1.2-ayatanaappindicator3-0.1 gir1.2-secret-1
./install.sh               # launcher, app menu entry, autostart
./install.sh --uninstall
```

Run `./install.sh` again after moving the checkout.

## Privacy

Translation sends the text to Google Translate. Fix English sends it to LanguageTool, or to Gemini if you pick it in settings and add a free [API key](https://aistudio.google.com/apikey). The key is kept in the GNOME keyring.

## Development

```sh
./bin/parley-tray                                       # run from the checkout
python3 -m parley_tray.backends.google "xin chào"       # try a backend on its own
python3 -m parley_tray.backends.languagetool "he go to office"
./build-deb.sh                                          # .deb and source tarball in dist/
```

Releases: bump `__version__` in `parley_tray/__init__.py`, commit, then push a matching `v<version>` tag; the workflow builds and publishes the release.

The window is GTK4 + libadwaita; the tray icon is a small GTK3 helper (`parley_tray/tray.py`) because AppIndicator can't live in a GTK4 process. The helper calls the app's actions over D-Bus.
