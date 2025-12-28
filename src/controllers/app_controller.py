class AppController:
    def __init__(self, **kwargs):

        # Обязательная зависимость
        self.db = kwargs.get('db_model')
        if not self.db:
            raise ValueError("db_model is required")

        # Опциональные зависимости
        self.serializer = kwargs.get('serializer')
        self.xml_serializer = kwargs.get('xml_serializer')
        self.validator = kwargs.get('validator')
        self.logger = kwargs.get('logger')
        self.os_module = kwargs.get('os_module')
        self.exporter = kwargs.get('exporter')
        self.importer = kwargs.get('importer')

        # UI функции
        self.show_info = kwargs.get('show_info', self._default_show_info)
        self.show_error = kwargs.get('show_error', self._default_show_error)
        self.show_warning = kwargs.get('show_warning', self._default_show_warning)
        self.ask_confirmation = kwargs.get('ask_confirmation', self._default_ask_confirmation)

        self.view = None
        self.root = None

    def _default_show_info(self, title, message):
        print(f"[INFO] {title}: {message}")

    def _default_show_error(self, title, message):
        print(f"[ERROR] {title}: {message}")

    def _default_show_warning(self, title, message):
        print(f"[WARNING] {title}: {message}")

    def _default_ask_confirmation(self, title, message):
        print(f"[CONFIRM] {title}: {message}")
        return True

    # --- Основные методы ---
    def set_view(self, view):
        self.view = view

    def set_root(self, root):
        self.root = root

    def save_data(self):
        """Сохранение данных"""
        self.show_info("Info", "Данные сохранены (через контроллер)")
        self.db._db.commit()
        if self.logger:
            self.logger.info("Data saved to database")

    # --- ЭКСПОРТ МЕТОДЫ (упрощенные) ---

    def export_json(self):
        """Экспорт групп в JSON"""
        if not self.exporter:
            self.show_error("Error", "Экспортер не доступен")
            return

        success, message = self.exporter.export_groups_to_json()
        if success:
            self.show_info("Export", message)
            if self.logger:
                self.logger.info(f"JSON export successful: {message}")
        else:
            self.show_error("Error", message)
            if self.logger:
                self.logger.error(f"JSON export failed: {message}")

    def export_xml_groups(self):
        """Экспорт групп в XML"""
        if not self.exporter:
            self.show_error("Error", "Экспортер не доступен")
            return

        success, message = self.exporter.export_groups_to_xml()
        if success:
            self.show_info("Export XML", message)
            if self.logger:
                self.logger.info(f"XML groups export successful: {message}")
        else:
            self.show_error("Error", message)
            if self.logger:
                self.logger.error(f"XML groups export failed: {message}")

    def export_xml_students(self):
        """Экспорт студентов в XML"""
        if not self.exporter:
            self.show_error("Error", "Экспортер не доступен")
            return

        success, message = self.exporter.export_students_to_xml()
        if success:
            self.show_info("Export XML", message)
            if self.logger:
                self.logger.info(f"XML students export successful: {message}")
        else:
            self.show_error("Error", message)
            if self.logger:
                self.logger.error(f"XML students export failed: {message}")

    def export_xml_journal(self):
        """Экспорт журнала в XML"""
        if not self.exporter:
            self.show_error("Error", "Экспортер не доступен")
            return

        success, message = self.exporter.export_journal_to_xml()
        if success:
            self.show_info("Export XML", message)
            if self.logger:
                self.logger.info(f"XML journal export successful: {message}")
        else:
            self.show_error("Error", message)
            if self.logger:
                self.logger.error(f"XML journal export failed: {message}")

    # Двоичная сериализация
    def export_pickle(self):
        """Экспорт всех данных в Pickle"""
        if not self.exporter:
            self.show_error("Error", "Экспортер не доступен")
            return

        success, message = self.exporter.export_full_backup_to_pickle()
        if success:
            self.show_info("Export Binary", message)
            if self.logger:
                self.logger.info(f"Pickle export successful: {message}")
        else:
            self.show_error("Error", message)
            if self.logger:
                self.logger.error(f"Pickle export failed: {message}")

    def export_msgpack(self):
        """Экспорт групп в MessagePack (бинарный, компактный)"""
        if not self.exporter:
            self.show_error("Error", "Экспортер не доступен")
            return

        success, message = self.exporter.export_groups_to_msgpack()
        if success:
            self.show_info("Export MessagePack", message)
            if self.logger:
                self.logger.info(f"MessagePack export successful: {message}")
        else:
            self.show_error("Error", message)
            if self.logger:
                self.logger.error(f"MessagePack export failed: {message}")

    # --- ИМПОРТ МЕТОДЫ ---

    def auto_detect_and_import(self, filename: str):
        """Автоматическое определение формата и импорт"""
        if not self.importer:
            self.show_error("Error", "Импортер не доступен")
            return

        if self.logger:
            self.logger.info(f"Starting auto-detect import for file: {filename}")

        success, message = self.importer.auto_detect_and_import(filename)

        # Обработка большого файла
        if success and message == "large_file":
            # В этом случае второй элемент кортежа - размер файла
            file_size = self.importer.auto_detect_and_import(filename)[1]
            confirm = self.ask_confirmation(
                "Large File",
                f"Файл очень большой ({file_size / 1024 / 1024:.1f} MB). Продолжить импорт?"
            )
            if confirm:
                # Повторяем импорт с подтверждением
                success, message = self.importer.auto_detect_and_import(filename)
            else:
                if self.logger:
                    self.logger.info("Import cancelled by user (large file)")
                return

        if success:
            self.show_info("Импорт завершен", message)
            if self.logger:
                self.logger.info(f"Import successful: {message}")
            # Обновляем представление после импорта
            if self.view:
                self.view.main_frame_reset(only_combobox_values=True)
        else:
            self.show_error("Import Error", message)
            if self.logger:
                self.logger.error(f"Import failed: {message}")

    @staticmethod
    def validate_year(self, year):
        from tkinter import messagebox as msg
        if not self.validator:
            msg.showwarning("Ошибка", "Валидатор не доступен")
            return False

        if not self.validator.is_valid_year(year):
            msg.showwarning("Ошибка", "Некорректный год")
            return False
        return True

    # Методы для работы с меню
    def open_date_window(self, action):
        if self.view:
            self.view.date_window(action)

    def open_group_window(self, action):
        if self.view:
            self.view.group_window(action)

    def open_student_window(self, action):
        if self.view:
            self.view.student_window(action)

    def open_lesson_window(self, action):
        if self.view:
            self.view.lesson_window(action)

    def open_about_window(self):
        if self.view:
            self.view.about_window()

    def open_about_author_window(self):
        if self.view:
            self.view.about_author_window()

    def open_test_data_window(self):
        if self.view:
            self.view.test_data_window()

    def open_db_clear_window(self):
        if self.view:
            self.view.db_clear_window()

    def close_program(self):
        """Закрыть программу"""
        self.db.close()
        if self.root:
            self.root.destroy()

    # Вспомогательные методы
    def get_groups(self):
        groups = self.db.having_individual_return("Groups", ["group"], ["group"])
        return [g[0] for g in groups] if groups else []

    def get_students(self):
        students = self.db.having_individual_return(
            "Students",
            ["group", "surname", "name", "patronymic"],
            ["group", "surname", "name", "patronymic"]
        )
        return students if students else []

    def get_lessons(self):
        lessons = self.db.having_individual_return("Lessons", ["lesson"], ["lesson"])
        return [le[0] for le in lessons] if lessons else []

    # Методы для операций с БД
    def insert_date(self, year, month, day):
        return self.db.insert_date(year, month, day)

    def update_date(self, old_year, old_month, old_day, new_year, new_month, new_day):
        return self.db.update_date(old_year, old_month, old_day, new_year, new_month, new_day)

    def delete_date(self, year, month, day):
        return self.db.delete_date(year, month, day)

    def insert_group(self, group_name):
        return self.db.insert_group(group_name)

    def update_group(self, old_name, new_name):
        return self.db.update_group(old_name, new_name)

    def delete_group(self, group_name):
        return self.db.delete_group(group_name)

    def insert_student(self, group, surname, name, patronymic):
        return self.db.insert_student(group, surname, name, patronymic)

    def update_student(self, old_group, old_surname, old_name, old_patronymic,
                       new_group, new_surname, new_name, new_patronymic):
        return self.db.update_student(old_group, old_surname, old_name, old_patronymic,
                                      new_group, new_surname, new_name, new_patronymic)

    def delete_student(self, group, surname, name, patronymic):
        return self.db.delete_student(group, surname, name, patronymic)

    def insert_lesson(self, lesson_name):
        return self.db.insert_lesson(lesson_name)

    def update_lesson(self, old_name, new_name):
        return self.db.update_lesson(old_name, new_name)

    def delete_lesson(self, lesson_name):
        return self.db.delete_lesson(lesson_name)

    def insert_test_data(self):
        return self.db.test_data()

    def clear_database(self):
        return self.db.clear()

    def main_frame_reset(self, only_combobox_values=False):
        if self.view:
            self.view.main_frame_reset(only_combobox_values)