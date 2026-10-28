"""Tray icon for Parley: a GTK3 helper, since AppIndicator can't share a process with GTK4.

Menu items run the main app's actions over D-Bus; the helper exits when the main app does.
"""

import os
import signal

import gi

gi.require_version("Gtk", "3.0")
for _mod in ("AyatanaAppIndicator3", "AppIndicator3"):
    try:
        gi.require_version(_mod, "0.1")
        AppIndicator = getattr(__import__("gi.repository", fromlist=[_mod]), _mod)
        break
    except (ValueError, ImportError):
        continue
else:
    raise SystemExit("parley-tray: install gir1.2-ayatanaappindicator3-0.1 for the tray icon")
from gi.repository import Gdk, Gio, Gtk  # noqa: E402

from . import APP_ID, OBJECT_PATH  # noqa: E402

ICONS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "icons")


def main():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    actions = Gio.DBusActionGroup.get(bus, APP_ID, OBJECT_PATH)

    def run(name):
        # A token lets the compositor focus the window instead of saying "Parley is ready".
        data = {}
        ctx = Gdk.Display.get_default().get_app_launch_context()
        token = ctx.get_startup_notify_id(None, [])
        if token:
            data["activation-token"] = token
        actions.activate_action_full(name, None, _vardict(data))

    menu = Gtk.Menu()
    first = None
    for label, name in (("Fix English", "fix"), ("Translate", "translate"), (None, None),
                        ("Settings", "settings"), ("Quit", "quit")):
        if label is None:
            menu.append(Gtk.SeparatorMenuItem())
            continue
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda _i, n=name: run(n))
        menu.append(item)
        first = first or item
    menu.show_all()

    indicator = AppIndicator.Indicator.new("parley-tray", "parley-tray-symbolic",
                                           AppIndicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_icon_theme_path(ICONS)
    indicator.set_title("Parley")
    indicator.set_menu(menu)
    indicator.set_secondary_activate_target(first)  # middle click
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

    Gio.bus_watch_name_on_connection(bus, APP_ID, Gio.BusNameWatcherFlags.NONE, None,
                                     lambda *_: Gtk.main_quit())
    signal.signal(signal.SIGTERM, lambda *_: Gtk.main_quit())
    signal.signal(signal.SIGINT, lambda *_: Gtk.main_quit())
    Gtk.main()


def _vardict(data: dict):
    from gi.repository import GLib

    return GLib.Variant("a{sv}", {k: GLib.Variant("s", v) for k, v in data.items()})


if __name__ == "__main__":
    main()
