class AppController:
    def __init__(self, **kwargs):

        # Обязательная зависимость
        self.db = kwargs.get('db_model')
        if not self.db:
            raise ValueError("db_model is required")

        self._state_applied = False
        self._spreadsheet_creation_pending = False

        # Опциональные зависимости
        self.serializer = kwargs.get('serializer')
        self.xml_serializer = kwargs.get('xml_serializer')
        self.validator = kwargs.get('validator')
        self.logger = kwargs.get('logger')
        self.os_module = kwargs.get('os_module')
        self.exporter = kwargs.get('exporter')
        self.importer = kwargs.get('importer')
        self.state_manager = kwargs.get('state_manager')

        # UI функции
        self.show_info = kwargs.get('show_info', self._default_show_info)
        self.show_error = kwargs.get('show_error', self._default_show_error)
        self.show_warning = kwargs.get('show_warning', self._default_show_warning)
        self.ask_confirmation = kwargs.get('ask_confirmation', self._default_ask_confirmation)

        self.view = None
        self.root = None

        self.current_state = {
            "selected_year": None,
            "selected_month": None,
            "selected_group": None,
            "selected_lesson": None,
            "window_geometry": None,
            "last_opened_tab": None
        }

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

    # --- Save State Методы ---
    def load_saved_state(self):
        """Загрузить сохраненное состояние"""
        if not self.state_manager:
            return

        saved_state = self.state_manager.load_state()
        if saved_state:
            self.current_state.update(saved_state)

            if self.logger:
                self.logger.info(f"Application state loaded: {self.current_state}")

    def apply_saved_state_to_ui(self):
        """Применить сохраненное состояние к пользовательскому интерфейсу"""
        # Если состояние уже применено, выходим
        if self._state_applied:
            return

        try:
            # Устанавливаем геометрию окна
            if self.current_state.get("window_geometry") and hasattr(self.view, 'root'):
                self.view.root.geometry(self.current_state["window_geometry"])

            # Ждем полной инициализации UI
            if hasattr(self.view, 'root'):
                # Даем время на инициализацию комбобоксов
                self.view.root.after(500, self._delayed_state_apply)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error applying saved state to UI: {e}")

    def _check_and_create_spreadsheet(self):
        """Проверить и создать таблицу если все значения выбраны"""
        if (hasattr(self.view, 'year') and self.view.year.get() and
                hasattr(self.view, 'month') and self.view.month.get() and
                hasattr(self.view, 'groups') and self.view.groups.get() and
                hasattr(self.view, 'lessons') and self.view.lessons.get()):

            # Вызываем фильтрацию чтобы создать таблицу
            if hasattr(self.view, 'filtering'):
                self.view.filtering()

    def save_current_state(self):
        """Сохранить текущее состояние"""
        try:
            # Сохраняем геометрию окна
            if hasattr(self.view, 'root') and self.view.root:
                self.current_state["window_geometry"] = self.view.root.geometry()

            # Сохраняем значения комбобоксов
            if hasattr(self.view, 'year'):
                self.current_state["selected_year"] = self.view.year.get()
            if hasattr(self.view, 'month'):
                self.current_state["selected_month"] = self.view.month.get()
            if hasattr(self.view, 'groups'):
                self.current_state["selected_group"] = self.view.groups.get()
            if hasattr(self.view, 'lessons'):
                self.current_state["selected_lesson"] = self.view.lessons.get()

            # Сохраняем состояние через state_manager
            if self.state_manager:
                self.state_manager.save_state(self.current_state)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving current state: {e}")

    def _create_table_from_state(self):
        """Создать таблицу из сохраненного состояния"""
        try:
            # Проверяем, что все значения действительно установлены
            if not (hasattr(self.view, 'year') and self.view.year.get() and
                    hasattr(self.view, 'month') and self.view.month.get() and
                    hasattr(self.view, 'groups') and self.view.groups.get() and
                    hasattr(self.view, 'lessons') and self.view.lessons.get()):
                self._state_applied = True
                return

            # Обновляем значения месяцев для выбранного года
            if self.view.year.get():
                self.view.month["values"] = [""] + self.view._get_date("month", self.view.year.get())

            # Вызываем создание таблицы напрямую - ОДИН РАЗ
            self._create_spreadsheet_directly()

            # Помечаем состояние как примененное
            self._state_applied = True
            self._spreadsheet_creation_pending = False

            if self.logger:
                self.logger.info(f"Spreadsheet created from saved state")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating table from state: {e}")
            self._state_applied = True
            self._spreadsheet_creation_pending = False

    def _delayed_state_apply(self):
        """Отложенное применение состояния (после инициализации UI)"""
        try:
            # Если состояние уже применено, выходим
            if self._state_applied:
                return

            # Помечаем, что начинаем применение состояния
            self._spreadsheet_creation_pending = True

            # Применяем значения только если они не пустые
            values_to_apply = []

            if hasattr(self.view, 'year') and self.current_state.get("selected_year"):
                self.view.year.set(self.current_state["selected_year"])
                values_to_apply.append("year")

            if hasattr(self.view, 'month') and self.current_state.get("selected_month"):
                self.view.month.set(self.current_state["selected_month"])
                values_to_apply.append("month")

            if hasattr(self.view, 'groups') and self.current_state.get("selected_group"):
                self.view.groups.set(self.current_state["selected_group"])
                values_to_apply.append("group")

            if hasattr(self.view, 'lessons') and self.current_state.get("selected_lesson"):
                self.view.lessons.set(self.current_state["selected_lesson"])
                values_to_apply.append("lesson")

            if self.logger:
                self.logger.info(f"Applied state values: {values_to_apply}")

            # Проверяем, что все 4 значения установлены
            if len(values_to_apply) == 4:
                # Если все значения установлены, ждем обновления UI и создаем таблицу
                self.view.root.after(800, self._create_table_from_state)
            else:
                # Помечаем состояние как примененное
                self._state_applied = True
                if self.logger:
                    self.logger.info(f"State partially applied: {len(values_to_apply)} values")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in delayed state apply: {e}")
            self._state_applied = True

    def _call_filtering_directly(self):
        """Прямой вызов filtering"""
        # Поскольку filtering определена как вложенная функция,
        # нужно получить к ней доступ через локальное пространство имен
        try:
            # Обновляем значения месяцев для выбранного года
            if self.view.year.get():
                self.view.month["values"] = [""] + self.view._get_date("month", self.view.year.get())

            # Сохраняем состояние
            self.current_state["selected_year"] = self.view.year.get()
            self.current_state["selected_month"] = self.view.month.get()
            self.current_state["selected_group"] = self.view.groups.get()
            self.current_state["selected_lesson"] = self.view.lessons.get()

            # Создаем таблицу если все значения установлены
            if all([self.view.year.get(), self.view.month.get(),
                    self.view.groups.get(), self.view.lessons.get()]):
                # Вызываем create_spreadsheet напрямую
                self._create_spreadsheet_directly()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calling filtering directly: {e}")

    def _create_spreadsheet_directly(self):
        """Создать таблицу напрямую"""
        try:
            colors = {
                "0": "#9EE2C0",
                "1": "#F5E2B5",
                "2": "#FF8477",
            }

            temp_journal = self.db.select_where(
                "Journal",
                ["date", "group", "surname", "name", "patronymic", "lesson", "missed_hours"],
                {
                    "date": f"{self.view.year.get()}-{self.view.month.get()}",
                    "group": self.view.groups.get(),
                    "lesson": self.view.lessons.get()
                },
                ["surname", "name", "patronymic", "date"]
            )

            if not temp_journal:
                if hasattr(self.view, 'root'):
                    # Показываем ошибку только если UI готов
                    self.show_error("Нет данных", "Нет данных для отображения")
                return

            days = []
            students = []
            spreadsheet_set_values = []
            temp_student = 0

            for i in temp_journal:
                day = i[0].split("-")[-1]
                student = f"{i[2]} {i[3]} {i[4]}"
                if student != temp_student:
                    temp_student = student
                    spreadsheet_set_values.append([])
                spreadsheet_set_values[-1].append(i[6])
                if day not in days:
                    days.append(day)
                if student not in students:
                    students.append(student)

            spreadsheet_width = len(days)
            spreadsheet_height = len(students)
            spreadsheet_cells_values = tuple(
                tuple(
                    ("-", 0, 1, 2)
                    for _ in range(spreadsheet_width)
                )
                for _ in range(spreadsheet_height)
            )

            # Создаем таблицу
            if hasattr(self.view, 'spreadsheet'):
                self.view.spreadsheet.create(
                    columns=spreadsheet_width,
                    rows=spreadsheet_height,
                    columns_headers=days,
                    rows_headers=students,
                    set_values=spreadsheet_set_values,
                    cells_values=spreadsheet_cells_values,
                    cells_colors=colors
                )

                if self.logger:
                    self.logger.info(f"Spreadsheet created with {len(students)} students and {len(days)} days")

            temp_journal.clear()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating spreadsheet: {e}")
            self.show_error("Ошибка", f"Не удалось создать таблицу: {str(e)}")

    def _generate_all_events(self):
        """Сгенерировать события для всех комбобоксов"""
        try:
            # Генерируем события выбора по очереди с задержкой
            if hasattr(self.view, 'year') and self.view.year.get():
                self.view.root.after(100, lambda: self.view.year.event_generate("<<ComboboxSelected>>"))

            if hasattr(self.view, 'month') and self.view.month.get():
                self.view.root.after(200, lambda: self.view.month.event_generate("<<ComboboxSelected>>"))

            if hasattr(self.view, 'groups') and self.view.groups.get():
                self.view.root.after(300, lambda: self.view.groups.event_generate("<<ComboboxSelected>>"))

            if hasattr(self.view, 'lessons') and self.view.lessons.get():
                self.view.root.after(400, lambda: self.view.lessons.event_generate("<<ComboboxSelected>>"))

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error generating events: {e}")

    def _check_and_create_table(self):
        """Проверить и создать таблицу"""
        try:
            # Проверяем все ли значения установлены
            if (hasattr(self.view, 'year') and self.view.year.get() and
                    hasattr(self.view, 'month') and self.view.month.get() and
                    hasattr(self.view, 'groups') and self.view.groups.get() and
                    hasattr(self.view, 'lessons') and self.view.lessons.get()):

                # Обновляем значения месяцев для выбранного года
                if self.view.year.get():
                    self.view.month["values"] = [""] + self.view._get_date("month", self.view.year.get())

                # Создаем таблицу
                self._create_spreadsheet_directly()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking and creating table: {e}")

    def clear_saved_state(self):
        """Очистить сохраненное состояние"""
        if self.state_manager:
            success = self.state_manager.clear_state()
            if success and self.logger:
                self.logger.info("Application state cleared")
            return success
        return False

    def get_state_info(self):
        """Получить информацию о сохраненном состоянии"""
        if self.state_manager:
            return self.state_manager.get_state_info()
        return {"exists": False}

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