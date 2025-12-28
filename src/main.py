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
    # Инициализация локализации
    I18n.load_locale("ru")

    # Инициализация логгера
    logger = setup_logger()
    logger.info("Starting AttendanceTracker application")

    # Инициализация менеджера состояния
    state_manager = StateManager()

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

    # Создание представления
    app = MainWindow(controller)

    # Связывание контроллера и представления
    controller.set_view(app)
    controller.set_root(app.root)

    logger.info("Application initialized successfully")

    try:
        # Загружаем сохраненное состояние
        controller.load_saved_state()

        # ИНИЦИАЛИЗИРУЕМ значения комбобоксов ПЕРЕД применением состояния
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


if __name__ == "__main__":
    main()