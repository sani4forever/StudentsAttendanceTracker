import json

class Serializer:
    @staticmethod
    def save_to_json(data: list, filename: str):
        """Сохраняет данные списка в JSON файл."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Serialization error: {e}")
            return False