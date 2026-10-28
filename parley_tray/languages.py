# Languages Parley offers as translation targets.
NAMES = {
    "ar": "Arabic", "bg": "Bulgarian", "bn": "Bangla", "cs": "Czech", "da": "Danish", "de": "German",
    "el": "Greek", "en": "English", "es": "Spanish", "fi": "Finnish", "fr": "French", "he": "Hebrew",
    "hi": "Hindi", "hr": "Croatian", "hu": "Hungarian", "id": "Indonesian", "it": "Italian",
    "ja": "Japanese", "kn": "Kannada", "ko": "Korean", "lt": "Lithuanian", "mr": "Marathi",
    "nl": "Dutch", "no": "Norwegian", "pl": "Polish", "pt": "Portuguese", "ro": "Romanian",
    "ru": "Russian", "sk": "Slovak", "sl": "Slovenian", "sv": "Swedish", "ta": "Tamil", "te": "Telugu",
    "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", "vi": "Vietnamese", "zh": "Chinese",
    "zh-Hant": "Chinese (Traditional)",
}

# Sorted by name, for dropdowns.
CODES = sorted(NAMES, key=NAMES.get)


def name(code: str) -> str:
    return NAMES.get(code) or NAMES.get(code.split("-")[0]) or code
