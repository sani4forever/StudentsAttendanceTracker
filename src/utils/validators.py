import re

class Validator:
    @staticmethod
    def is_valid_year(year: str) -> bool:
        # Проверка: 4 цифры, от 1900 до 2099
        pattern = r"^(19|20)\d{2}$"
        return bool(re.match(pattern, year))

    @staticmethod
    def is_valid_name(name: str) -> bool:
        # Только буквы (кириллица/латиница) и дефис
        pattern = r"^[a-zA-Zа-яА-ЯёЁ\-]+$"
        return bool(re.match(pattern, name))