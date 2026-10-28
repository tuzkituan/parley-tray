# Parley Tray

Translate text or fix your English from the GNOME top bar. The desktop sibling of the [Parley](https://github.com/tuzkituan/parley) browser extension.

| To | Do |
| --- | --- |
| Translate the selected text | **Super+T**, or Translate in the tray menu |
| Fix the English of the selected text | **Super+G**, or Fix English in the tray menu |
| Run again now | **Ctrl+Enter** |
| Copy the result and close | **Ctrl+Shift+C** |
| Close | **Esc** |

The window opens with the selected text (or the clipboard) already filled in and done. Translation goes into your language, or into English when the text is already in your language. In Fix English, changed words are underlined.

## Install

Needs GNOME with the AppIndicator extension (Ubuntu has it on by default) and:

```sh
sudo apt install python3-gi gir1.2-adw-1 gir1.2-ayatanaappindicator3-0.1 gir1.2-secret-1
./install.sh               # launcher, app menu entry, autostart, Super+T / Super+G
./install.sh --uninstall
```

Run `./install.sh` again after moving the checkout. If a shortcut is already taken it is skipped; set your own in Settings > Keyboard > Custom Shortcuts with the command `parley-tray --translate` or `parley-tray --fix`.

## Privacy

Translation sends the text to Google Translate. Fix English sends it to LanguageTool, or to Gemini if you pick it in settings and add a free [API key](https://aistudio.google.com/apikey). The key is kept in the GNOME keyring.

## Development

```sh
./bin/parley-tray                                       # run from the checkout
python3 -m parley_tray.backends.google "xin chào"       # try a backend on its own
python3 -m parley_tray.backends.languagetool "he go to office"
```

The window is GTK4 + libadwaita; the tray icon is a small GTK3 helper (`parley_tray/tray.py`) because AppIndicator can't live in a GTK4 process. The helper calls the app's actions over D-Bus.
