# Super+T / Super+G as GNOME custom shortcuts, set up on first run so a .deb install gets them too.
import os
import shutil

from gi.repository import Gio

KEYS = "org.gnome.settings-daemon.plugins.media-keys"
BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
SHORTCUTS = [
    ("parley-translate", "Parley: Translate", "<Super>t", "--translate"),
    ("parley-fix", "Parley: Fix English", "<Super>g", "--fix"),
]


def _source():
    return Gio.SettingsSchemaSource.get_default()


def _custom(path: str) -> Gio.Settings:
    return Gio.Settings.new_with_path(f"{KEYS}.custom-keybinding", path)


def _taken(skip: set[str]) -> set[str]:
    """Every binding already in use, lowercased."""
    used = set()
    for path in Gio.Settings.new(KEYS).get_strv("custom-keybindings"):
        if path not in skip:
            used.add(_custom(path).get_string("binding").lower())
    for schema in ("org.gnome.desktop.wm.keybindings", "org.gnome.shell.keybindings", KEYS):
        if not _source().lookup(schema, True):
            continue
        s = Gio.Settings.new(schema)
        for key in s.props.settings_schema.list_keys():
            value = s.get_value(key)
            if value.get_type_string() == "as":
                used.update(v.lower() for v in value.unpack())
    return used


def install() -> list[str]:
    """Add the shortcuts whose keys are free; returns what was set or skipped, for the log."""
    if not _source().lookup(KEYS, True):
        return ["no GNOME media-keys settings, shortcuts skipped"]
    bin_ = os.environ.get("PARLEY_TRAY_BIN") or shutil.which("parley-tray") or "parley-tray"
    keys = Gio.Settings.new(KEYS)
    paths = keys.get_strv("custom-keybindings")
    ours = {f"{BASE}/{id_}/" for id_, *_ in SHORTCUTS}
    taken = _taken(ours)
    log = []
    for id_, name, binding, flag in SHORTCUTS:
        path = f"{BASE}/{id_}/"
        if binding.lower() in taken:
            log.append(f"{binding} already used, {name} skipped")
            continue
        s = _custom(path)
        s.set_string("name", name)
        s.set_string("binding", binding)
        s.set_string("command", f"{bin_} {flag}")
        if path not in paths:
            paths.append(path)
        log.append(f"{binding}: {name}")
    keys.set_strv("custom-keybindings", paths)
    return log


def remove() -> None:
    if not _source().lookup(KEYS, True):
        return
    keys = Gio.Settings.new(KEYS)
    for id_, *_ in SHORTCUTS:
        path = f"{BASE}/{id_}/"
        _custom(path).reset("name")
        _custom(path).reset("binding")
        _custom(path).reset("command")
    keys.set_strv("custom-keybindings",
                  [p for p in keys.get_strv("custom-keybindings") if p not in {f"{BASE}/{i}/" for i, *_ in SHORTCUTS}])
