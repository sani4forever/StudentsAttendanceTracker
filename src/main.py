import os
from tkinter import messagebox

from src.models.database import DatabaseWork
from src.views.main_window import MainWindow
from src.controllers.app_controller import AppController
from src.utils.i18n import I18n
from src.utils.serializer import Serializer
from src.utils.xml_serializer import XMLSerializer
from src.utils.validators import Validator
from src.utils.logger import setup_logger
from src.models.exporter import DataExporter
from src.models.importer import DataImporter
from src.utils.state_manager import StateManager


def main():
    # Инициализация менеджера состояния ПЕРВЫМ ДЕЛОМ
    state_manager = StateManager()

    # Загружаем состояние ДО инициализации локализации
    saved_state = None
    try:
        saved_state = state_manager.load_state()
    except Exception as e:
        print(f"Error loading state: {e}")

    # Определяем язык для загрузки
    default_language = "ru"
    if saved_state and "language" in saved_state:
        default_language = saved_state["language"]
        print(f"Loading saved language: {default_language}")

    # Инициализация локализации с правильным языком
    I18n.load_locale(default_language)

    # Инициализация логгера
    logger = setup_logger()
    logger.info(f"Starting AttendanceTracker application (language: {default_language})")

    # Инициализация менеджера состояния
    #state_manager = StateManager()

    # Проверка и создание директорий
    db_path = os.path.join(os.path.dirname(__file__), "../data/journal.db")
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
        logger.info(f"Created data directory: {os.path.dirname(db_path)}")

    # Создание экземпляров зависимостей
    db = DatabaseWork(db_path)
    db.create()
    logger.info(f"Database initialized at: {db_path}")

    serializer = Serializer()
    xml_serializer = XMLSerializer()
    validator = Validator()

    exporter = DataExporter(db, serializer, xml_serializer, os)
    importer = DataImporter(db, serializer, xml_serializer, os)

    # Создание контроллера с ВСЕМИ зависимостями через kwargs
    controller = AppController(
        db_model=db,
        exporter=exporter,
        importer=importer,
        serializer=serializer,
        xml_serializer=xml_serializer,
        validator=validator,
        logger=logger,
        show_info=messagebox.showinfo,
        show_error=messagebox.showerror,
        show_warning=messagebox.showwarning,
        ask_confirmation=messagebox.askyesno,
        os_module=os,
        state_manager = state_manager
    )

    if saved_state:
        controller.current_state.update(saved_state)

    # Создание представления
    app = MainWindow(controller)

    # Связывание контроллера и представления
    controller.set_view(app)
    controller.set_root(app.root)

    logger.info("Application initialized successfully")

    try:
        # ИНИЦИАЛИЗИРУЕМ значения комбобоксов
        app._initial_main_frame_setup()

        # Применяем сохраненное состояние СРАЗУ после инициализации UI
        controller.apply_saved_state_to_ui()

        # Запускаем приложение
        logger.info("Application started")
        app.start()

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise
    finally:
        # Сохраняем состояние только если приложение еще не закрыто
        try:
            if hasattr(controller, 'save_current_state') and controller.root:
                controller.save_current_state()
        except Exception as e:
            logger.error(f"Error saving state on shutdown: {e}")

        db.close()
        logger.info("Application shutdown")

    def restart_application():
        """Перезапустить приложение"""
        import sys
        import subprocess

        # Закрываем текущее приложение
        if 'app' in locals():
            app.root.destroy()

        # Запускаем новое окно
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()


if __name__ == "__main__":
    main()