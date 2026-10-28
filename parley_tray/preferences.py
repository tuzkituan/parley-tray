from gi.repository import Adw, Gtk

from . import languages, settings

PROOFREADERS = [("languagetool", "LanguageTool (no setup)"), ("gemini", "Gemini (your API key)")]


class Preferences(Adw.PreferencesDialog):
    def __init__(self, current: dict):
        super().__init__(title="Settings")
        page = Adw.PreferencesPage()
        self.add(page)

        translate = Adw.PreferencesGroup(title="Translate",
                                         description="Text is sent to Google Translate.")
        page.add(translate)
        self.target = self._language_row("Translate into", current["target"])
        self.fallback = self._language_row("Text already in that language goes into", current["fallback"])
        translate.add(self.target)
        translate.add(self.fallback)

        fix = Adw.PreferencesGroup(title="Fix English",
                                   description="Text is sent to the service you pick.")
        page.add(fix)
        self.proofreader = Adw.ComboRow(title="Proofreader",
                                        model=Gtk.StringList.new([label for _, label in PROOFREADERS]))
        self.proofreader.set_selected([k for k, _ in PROOFREADERS].index(current["proofreader"]))
        self.key = Adw.PasswordEntryRow(title="Gemini API key", text=settings.gemini_key())
        self.model = Adw.EntryRow(title="Gemini model", text=current["gemini_model"])
        link = Gtk.LinkButton(uri="https://aistudio.google.com/apikey", label="Get a free key",
                              valign=Gtk.Align.CENTER)
        self.key.add_suffix(link)
        for row in (self.proofreader, self.key, self.model):
            fix.add(row)
        self.proofreader.connect("notify::selected", lambda *_: self._sync())
        self._sync()

        self.connect("closed", lambda *_: self._save())

    def _language_row(self, title: str, code: str) -> Adw.ComboRow:
        row = Adw.ComboRow(title=title, model=Gtk.StringList.new([languages.name(c) for c in languages.CODES]),
                           enable_search=True)
        row.set_selected(languages.CODES.index(code) if code in languages.CODES else 0)
        return row

    def _sync(self):
        gemini = PROOFREADERS[self.proofreader.get_selected()][0] == "gemini"
        self.key.set_visible(gemini)
        self.model.set_visible(gemini)

    def _save(self):
        settings.save(
            target=languages.CODES[self.target.get_selected()],
            fallback=languages.CODES[self.fallback.get_selected()],
            proofreader=PROOFREADERS[self.proofreader.get_selected()][0],
            gemini_model=self.model.get_text().strip() or settings.defaults()["gemini_model"],
        )
        if self.key.get_text().strip() != settings.gemini_key():
            settings.save_gemini_key(self.key.get_text())
