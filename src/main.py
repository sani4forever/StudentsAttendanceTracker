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


def main():
    # Инициализация локализации
    I18n.load_locale("ru")

    # Инициализация логгера
    logger = setup_logger()
    logger.info("Starting AttendanceTracker application")

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
        os_module=os
    )

    # Создание представления
    app = MainWindow(controller)

    # Связывание контроллера и представления
    controller.set_view(app)
    controller.set_root(app.root)

    logger.info("Application initialized successfully")

    try:
        app.start()
        logger.info("Application started")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logger.info("Application shutdown")


if __name__ == "__main__":
    main()