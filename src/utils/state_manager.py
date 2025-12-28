import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger()


class StateManager:
    """Менеджер для сохранения и восстановления состояния приложения"""

    def __init__(self, app_name: str = "AttendanceTracker"):
        self.app_name = app_name
        self.state_dir = self._get_state_directory()
        self.state_file = os.path.join(self.state_dir, "app_state.json")

    def _get_state_directory(self) -> str:
        """Получить директорию для сохранения состояния"""
        # Для Windows
        if os.name == 'nt':
            appdata = os.getenv('APPDATA')
            state_dir = os.path.join(appdata, self.app_name, "state")
        # Для Linux/Mac
        else:
            home = os.path.expanduser("~")
            state_dir = os.path.join(home, f".{self.app_name.lower()}", "state")

        # Создаем директорию, если не существует
        os.makedirs(state_dir, exist_ok=True)
        return state_dir

    def save_state(self, state_data: Dict[str, Any]) -> bool:
        """Сохранить состояние приложения"""
        try:
            # Добавляем метаданные
            full_state = {
                "state": state_data,
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "app_version": "1.0.0"
                }
            }

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(full_state, f, indent=2, ensure_ascii=False)

            logger.info(f"Состояние сохранено: {self.state_file}")
            return True

        except Exception as e:
            logger.error(f"Ошибка сохранения состояния: {e}")
            return False

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Загрузить состояние приложения"""
        try:
            if not os.path.exists(self.state_file):
                logger.info("Файл состояния не найден, используется состояние по умолчанию")
                return None

            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Проверяем структуру файла
            if "state" not in data:
                logger.warning("Некорректная структура файла состояния")
                return None

            logger.info(f"Состояние загружено: {self.state_file}")
            return data["state"]

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения JSON состояния: {e}")
            # Создаем резервную копию поврежденного файла
            self._backup_corrupted_file()
            return None
        except Exception as e:
            logger.error(f"Ошибка загрузки состояния: {e}")
            return None

    def _backup_corrupted_file(self):
        """Создать резервную копию поврежденного файла состояния"""
        try:
            if os.path.exists(self.state_file):
                backup_file = f"{self.state_file}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.state_file, backup_file)
                logger.info(f"Создана резервная копия поврежденного файла: {backup_file}")
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")

    def clear_state(self) -> bool:
        """Очистить сохраненное состояние"""
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
                logger.info("Состояние очищено")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка очистки состояния: {e}")
            return False

    def get_state_info(self) -> Dict[str, Any]:
        """Получить информацию о сохраненном состоянии"""
        if not os.path.exists(self.state_file):
            return {"exists": False}

        try:
            stat_info = os.stat(self.state_file)
            return {
                "exists": True,
                "file_size": stat_info.st_size,
                "modified_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "file_path": self.state_file
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о состоянии: {e}")
            return {"exists": False}