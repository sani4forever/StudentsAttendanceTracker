import json
import pickle
import msgpack
import os


class Serializer:
    @staticmethod
    def save_to_json(data: list, filename: str) -> bool:
        """Сохраняет данные списка в JSON файл."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"JSON serialization error: {e}")
            return False

    @staticmethod
    def load_from_json(filename: str):
        """Загружает данные из JSON файла."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"JSON deserialization error: {e}")
            return None

    # Двоичная сериализация - Pickle
    @staticmethod
    def save_to_pickle(data, filename: str) -> bool:
        """Сохраняет данные в бинарный формат Pickle."""
        try:
            with open(filename, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            print(f"Pickle serialization error: {e}")
            return False

    @staticmethod
    def load_from_pickle(filename: str):
        """Загружает данные из Pickle файла."""
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Pickle deserialization error: {e}")
            return None

    # Двоичная сериализация - MessagePack
    @staticmethod
    def save_to_msgpack(data, filename: str) -> bool:
        """Сохраняет данные в бинарный формат MessagePack."""
        try:
            with open(filename, 'wb') as f:
                f.write(msgpack.packb(data))
            return True
        except Exception as e:
            print(f"MessagePack serialization error: {e}")
            return False

    @staticmethod
    def load_from_msgpack(filename: str):
        """Загружает данные из MessagePack файла."""
        try:
            with open(filename, 'rb') as f:
                return msgpack.unpackb(f.read(), raw=False)
        except Exception as e:
            print(f"MessagePack deserialization error: {e}")
            return None

    # Утилитный метод
    @staticmethod
    def get_file_info(filename: str) -> dict:
        """Возвращает информацию о файле."""
        if not os.path.exists(filename):
            return None

        stats = os.stat(filename)
        return {
            'size': stats.st_size,
            'created': stats.st_ctime,
            'modified': stats.st_mtime,
            'is_binary': filename.endswith(('.pkl', '.msgpack', '.bin'))
        }

    def detect_format(filename: str) -> str:
        """Определяет формат файла по расширению."""
        import os
        ext = os.path.splitext(filename)[1].lower()
        format_map = {
            '.json': 'json',
            '.pkl': 'pickle',
            '.pickle': 'pickle',
            '.msgpack': 'msgpack',
            '.xml': 'xml'
        }
        return format_map.get(ext, 'unknown')