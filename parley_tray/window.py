import threading

from gi.repository import Adw, Gdk, GLib, Gtk, Pango

from . import diff, languages, settings
from .backends import EngineError, gemini, google, languagetool

# Wait this long after the last keystroke before running again.
DEBOUNCE_MS = 600


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        # Hidden on close and reused: the app keeps this window for its whole life.
        super().__init__(application=app, title="Parley", default_width=520, default_height=420,
                         hide_on_close=True)
        self._seq = 0  # bumped per run, so a slow answer can't overwrite a newer one
        self._debounce = 0
        self._prefill_pending = False
        self._result = ""

        self.mode = Adw.ToggleGroup()
        self.mode.add(Adw.Toggle(name="fix", label="Fix English"))
        self.mode.add(Adw.Toggle(name="translate", label="Translate"))
        self.mode.connect("notify::active-name", lambda *_: self._mode_changed())

        settings_button = Gtk.Button(icon_name="emblem-system-symbolic", tooltip_text="Settings")
        settings_button.connect("clicked", lambda *_: self.open_settings())
        header = Adw.HeaderBar(title_widget=self.mode)
        header.pack_end(settings_button)

        self.banner = Adw.Banner()

        self.input = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, top_margin=10, bottom_margin=10,
                                  left_margin=12, right_margin=12)
        self.input.get_buffer().connect("changed", lambda *_: self._schedule())
        self.input.update_property([Gtk.AccessibleProperty.LABEL], ["Text"])

        self.output = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, editable=False, cursor_visible=False,
                                   top_margin=10, bottom_margin=10, left_margin=12, right_margin=12)
        self.output.update_property([Gtk.AccessibleProperty.LABEL], ["Result"])
        self._changed_tag = self.output.get_buffer().create_tag(
            "changed", weight=Pango.Weight.BOLD, underline=Pango.Underline.SINGLE)

        self.status = Gtk.Label(xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END, css_classes=["dim-label"])
        self.spinner = Adw.Spinner(visible=False)
        self.target = Gtk.DropDown.new_from_strings([languages.name(c) for c in languages.CODES])
        self.target.set_tooltip_text("Translate into")
        self.target.connect("notify::selected", lambda *_: self._target_changed())

        self.copy = Gtk.Button(label="Copy", css_classes=["suggested-action"], sensitive=False,
                               tooltip_text="Copy and close (Ctrl+Shift+C)")
        self.copy.connect("clicked", lambda *_: self.copy_and_close())

        middle = Gtk.Box(spacing=8)
        middle.append(self.spinner)
        middle.append(self.status)
        middle.append(self.target)

        bottom = Gtk.Box(halign=Gtk.Align.END)
        bottom.append(self.copy)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=6, margin_bottom=12,
                       margin_start=12, margin_end=12)
        body.append(_card(self.input))
        body.append(middle)
        body.append(_card(self.output))
        body.append(bottom)

        view = Adw.ToolbarView(content=body)
        view.add_top_bar(header)
        view.add_top_bar(self.banner)
        self.set_content(view)

        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self._key)
        self.add_controller(keys)
        self.connect("notify::is-active", lambda *_: self._maybe_prefill())
        self.connect("close-request", self._closing)

        self.settings = settings.load()
        self._select_target(self.settings["target"])
        self._mode_changed()

    # Opening

    def open(self, mode: str):
        """Switch to mode and fill the input from the selection once this window has focus."""
        self.mode.set_active_name(mode)
        self._prefill_pending = True
        self.present()
        self._maybe_prefill()

    def _maybe_prefill(self):
        # Wayland only hands the selection to the focused window.
        if not (self._prefill_pending and self.is_active()):
            return
        self._prefill_pending = False
        display = self.get_display()
        self._read(display.get_primary_clipboard(), lambda: self._read(display.get_clipboard(), None))

    def _read(self, clipboard: Gdk.Clipboard, otherwise):
        def done(cb, res):
            try:
                text = cb.read_text_finish(res)
            except GLib.Error:
                text = None
            if text and text.strip():
                self._fill(text.strip())
            elif otherwise:
                otherwise()

        clipboard.read_text_async(None, done)

    def _fill(self, text: str):
        buf = self.input.get_buffer()
        buf.set_text(text)
        # Selected, so typing replaces it.
        buf.select_range(buf.get_start_iter(), buf.get_end_iter())
        self.input.grab_focus()
        self.run()

    # Running

    def _text(self) -> str:
        buf = self.input.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()

    def _schedule(self):
        if self._debounce:
            GLib.source_remove(self._debounce)
        self._debounce = GLib.timeout_add(DEBOUNCE_MS, self._debounced)

    def _debounced(self):
        self._debounce = 0
        self.run()
        return GLib.SOURCE_REMOVE

    def run(self):
        if self._debounce:
            GLib.source_remove(self._debounce)
            self._debounce = 0
        self._seq += 1
        seq, text, mode, s = self._seq, self._text(), self.mode.get_active_name(), self.settings
        self.banner.set_revealed(False)
        if not text:
            self._show(seq, "", None, self._idle_status())
            return
        self.spinner.set_visible(True)
        key = settings.gemini_key() if mode == "fix" and s["proofreader"] == "gemini" else ""

        def work():
            try:
                if mode == "translate":
                    out, source, into = google.translate(text, s["target"], s["fallback"])
                    status = f"{languages.name(source)} → {languages.name(into)}"
                    GLib.idle_add(self._show, seq, out, None, status)
                else:
                    fixed = gemini.fix(text, key, s["gemini_model"]) if s["proofreader"] == "gemini" \
                        else languagetool.fix(text)
                    status = "No mistakes found" if fixed == text else "Fixed"
                    GLib.idle_add(self._show, seq, fixed, text, status)
            except EngineError as e:
                GLib.idle_add(self._fail, seq, str(e))
            except Exception as e:  # a bug, but still say something
                GLib.idle_add(self._fail, seq, f"Something went wrong: {e}")

        threading.Thread(target=work, daemon=True).start()

    def _show(self, seq: int, out: str, before: str | None, status: str):
        if seq != self._seq:
            return
        self.spinner.set_visible(False)
        self.status.set_label(status)
        buf = self.output.get_buffer()
        buf.set_text("")
        if before is None:
            buf.set_text(out)
        else:
            for piece, changed in diff.changes(before, out):
                end = buf.get_end_iter()
                if changed:
                    buf.insert_with_tags(end, piece, self._changed_tag)
                else:
                    buf.insert(end, piece)
        self._result = out
        self.copy.set_sensitive(bool(out))

    def _fail(self, seq: int, message: str):
        if seq != self._seq:
            return
        self.spinner.set_visible(False)
        self.status.set_label(self._idle_status())
        self.banner.set_title(message)
        self.banner.set_revealed(True)

    def _idle_status(self) -> str:
        if self.mode.get_active_name() == "translate":
            return "Translate into"
        return "Gemini" if self.settings["proofreader"] == "gemini" else "LanguageTool"

    # Controls

    def _mode_changed(self):
        self.target.set_visible(self.mode.get_active_name() == "translate")
        self.run()

    def _select_target(self, code: str):
        if code in languages.CODES:
            self.target.set_selected(languages.CODES.index(code))

    def _target_changed(self):
        code = languages.CODES[self.target.get_selected()]
        if code != self.settings["target"]:
            self.settings = settings.save(target=code)
            self.run()

    def copy_and_close(self):
        if not self._result:
            return
        self.get_display().get_clipboard().set(self._result)
        # Let the clipboard reach the compositor before the window goes.
        GLib.timeout_add(150, lambda: self.close() and False)

    def open_settings(self):
        from .preferences import Preferences

        dialog = Preferences(self.settings)
        dialog.connect("closed", lambda *_: self._settings_changed())
        dialog.present(self)

    def _settings_changed(self):
        self.settings = settings.load()
        self._select_target(self.settings["target"])
        self.run()

    def _key(self, _ctrl, keyval, _code, state):
        mods = state & Gtk.accelerator_get_default_mod_mask()
        ctrl = Gdk.ModifierType.CONTROL_MASK
        if keyval == Gdk.KEY_Escape and not mods:
            self.close()
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and mods == ctrl:
            self.run()
        elif keyval in (Gdk.KEY_c, Gdk.KEY_C) and mods == ctrl | Gdk.ModifierType.SHIFT_MASK:
            self.copy_and_close()
        else:
            return False
        return True

    def _closing(self, *_):
        self._seq += 1
        if self._debounce:
            GLib.source_remove(self._debounce)
            self._debounce = 0
        return False


def _card(child: Gtk.Widget) -> Gtk.Widget:
    scroller = Gtk.ScrolledWindow(child=child, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
    return Gtk.Frame(child=scroller, css_classes=["view"])
