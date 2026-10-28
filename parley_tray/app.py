import os
import subprocess
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib  # noqa: E402

from . import APP_ID, __version__, settings, shortcuts  # noqa: E402

USAGE = """parley-tray [--translate | --fix | --settings | --background | --quit | --remove-shortcuts | --version]

Stays in the tray. With no option, opens the window on Fix English.
"""


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None
        self.tray = None
        self.quitting = False
        for name, handler in (("translate", lambda *_: self.show("translate")),
                              ("fix", lambda *_: self.show("fix")),
                              ("settings", lambda *_: self.show_settings()),
                              ("quit", lambda *_: self.stop())):
            action = Gio.SimpleAction(name=name)
            action.connect("activate", handler)
            self.add_action(action)

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.hold()  # resident: closing the window keeps the tray
        self.spawn_tray()
        if not settings.load()["shortcuts"]:
            for line in shortcuts.install():
                print(f"parley-tray: {line}")
            settings.save(shortcuts=True)

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        flag = args[0] if args else ""
        if flag in ("-h", "--help"):
            command_line.print_literal(USAGE)
        elif flag == "--background":
            pass
        elif flag == "--quit":
            self.stop()
        elif flag == "--settings":
            self.show_settings()
        elif flag in ("", "--translate", "--fix"):
            self.show("translate" if flag == "--translate" else "fix")
        else:
            command_line.printerr_literal(USAGE)
            return 2
        return 0

    def show(self, mode: str):
        from .window import Window

        if self.window is None:
            self.window = Window(self)
        self.window.open(mode)

    def show_settings(self):
        self.show("fix")
        self.window.open_settings()

    # The tray icon is a GTK3 helper: AppIndicator can't live in a GTK4 process.
    def spawn_tray(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = {**os.environ, "PYTHONPATH": root}
        self.tray = subprocess.Popen([sys.executable, "-m", "parley_tray.tray"], env=env)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, self.tray.pid, self._tray_gone)

    def _tray_gone(self, _pid, status):
        if not self.quitting and os.waitstatus_to_exitcode(status) != 0:
            GLib.timeout_add_seconds(2, lambda: self.spawn_tray() and False)

    def stop(self):
        self.quitting = True
        if self.tray and self.tray.poll() is None:
            self.tray.terminate()
        self.quit()


def main() -> int:
    GLib.set_prgname("parley-tray")
    GLib.set_application_name("Parley")
    # These don't need the running instance.
    if sys.argv[1:] == ["--version"]:
        print(f"parley-tray {__version__}")
        return 0
    if sys.argv[1:] == ["--remove-shortcuts"]:
        shortcuts.remove()
        settings.save(shortcuts=True)
        return 0
    return App().run(sys.argv)
