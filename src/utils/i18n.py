import json
import os

class I18n:
    _translations = {}

    @staticmethod
    def load_locale(lang_code="ru"):
        path = os.path.join(os.path.dirname(__file__), f"../resources/locales/{lang_code}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                I18n._translations = json.load(f)
        except FileNotFoundError:
            print(f"Locale {lang_code} not found.")
            I18n._translations = {}

    @staticmethod
    def get(key):
        return I18n._translations.get(key, key)

# Глобальная вспомогательная функция
def _(key):
    return I18n.get(key)