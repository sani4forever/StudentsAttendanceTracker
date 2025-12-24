import os


from src.models.database import DatabaseWork
from src.views.main_window import MainWindow
from src.controllers.app_controller import AppController
from src.utils.i18n import I18n

def main():
    I18n.load_locale("en")

    db_path = os.path.join(os.path.dirname(__file__), "../data/journal.db")
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))

    db = DatabaseWork(db_path)
    db.create()

    controller = AppController(db)

    app = MainWindow(controller)

    controller.set_view(app)

    try:
        app.start()
    finally:
        db.close()


if __name__ == "__main__":
    main()