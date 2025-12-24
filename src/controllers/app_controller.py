from tkinter import messagebox

from src.utils.serializer import Serializer
from src.utils.validators import Validator

class AppController:
    def __init__(self, db_model):
        self.db = db_model
        self.view = None
        self.root = None

    def set_view(self, view):
        self.view = view

    def set_root(self, root):
        self.root = root

    def save_data(self):
        messagebox.showinfo("Info", "Данные сохранены (через контроллер)")
        self.db._db.commit()

    def export_json(self):
        data = self.db.having_individual_return("Groups", ["group"])
        if Serializer.save_to_json(data, "groups_export.json"):
            messagebox.showinfo("Export", "Группы экспортированы в JSON")
        else:
            messagebox.showerror("Error", "Ошибка экспорта")

    @staticmethod
    def validate_year(year):
        if not Validator.is_valid_year(year):
            messagebox.showwarning("Ошибка", "Некорректный год")
            return False
        return True

    # Методы для работы с меню
    def open_date_window(self, action):
        """Открыть окно для работы с датами"""
        self.view.date_window(action)

    def open_group_window(self, action):
        """Открыть окно для работы с группами"""
        self.view.group_window(action)

    def open_student_window(self, action):
        """Открыть окно для работы со студентами"""
        self.view.student_window(action)

    def open_lesson_window(self, action):
        """Открыть окно для работы с занятиями"""
        self.view.lesson_window(action)

    def open_about_window(self):
        """Открыть окно 'О программе'"""
        self.view.about_window()

    def open_about_author_window(self):
        """Открыть окно 'Об авторе'"""
        self.view.about_author_window()

    def open_test_data_window(self):
        """Открыть окно для вставки тестовых данных"""
        self.view.test_data_window()

    def open_db_clear_window(self):
        """Открыть окно для очистки БД"""
        self.view.db_clear_window()

    def close_program(self):
        """Закрыть программу"""
        self.db.close()
        if self.root:
            self.root.destroy()

    # Вспомогательные методы для работы с данными
    @staticmethod
    def get_date(date_type="year", year=None):
        """Получить список дат из БД"""
        # Здесь нужно реализовать логику получения дат из БД
        # Это упрощенный пример
        if date_type == "year":
            return ["2024", "2023", "2022"]
        elif date_type == "month" and year:
            return ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        return []

    def get_groups(self):
        """Получить список групп"""
        groups = self.db.having_individual_return("Groups", ["group"], ["group"])
        return [g[0] for g in groups] if groups else []

    def get_students(self):
        """Получить список студентов"""
        students = self.db.having_individual_return(
            "Students",
            ["group", "surname", "name", "patronymic"],
            ["group", "surname", "name", "patronymic"]
        )
        return students if students else []

    def get_lessons(self):
        """Получить список занятий"""
        lessons = self.db.having_individual_return("Lessons", ["lesson"], ["lesson"])
        return [le[0] for le in lessons] if lessons else []

    # Методы для операций с БД
    def insert_date(self, year, month, day):
        """Вставить дату"""
        return self.db.insert_date(year, month, day)

    def update_date(self, old_year, old_month, old_day, new_year, new_month, new_day):
        """Обновить дату"""
        return self.db.update_date(old_year, old_month, old_day, new_year, new_month, new_day)

    def delete_date(self, year, month, day):
        """Удалить дату"""
        return self.db.delete_date(year, month, day)

    def insert_group(self, group_name):
        """Добавить группу"""
        return self.db.insert_group(group_name)

    def update_group(self, old_name, new_name):
        """Обновить группу"""
        return self.db.update_group(old_name, new_name)

    def delete_group(self, group_name):
        """Удалить группу"""
        return self.db.delete_group(group_name)

    def insert_student(self, group, surname, name, patronymic):
        """Добавить студента"""
        return self.db.insert_student(group, surname, name, patronymic)

    def update_student(self, old_group, old_surname, old_name, old_patronymic,
                      new_group, new_surname, new_name, new_patronymic):
        """Обновить студента"""
        return self.db.update_student(old_group, old_surname, old_name, old_patronymic,
                                     new_group, new_surname, new_name, new_patronymic)

    def delete_student(self, group, surname, name, patronymic):
        """Удалить студента"""
        return self.db.delete_student(group, surname, name, patronymic)

    def insert_lesson(self, lesson_name):
        """Добавить занятие"""
        return self.db.insert_lesson(lesson_name)

    def update_lesson(self, old_name, new_name):
        """Обновить занятие"""
        return self.db.update_lesson(old_name, new_name)

    def delete_lesson(self, lesson_name):
        """Удалить занятие"""
        return self.db.delete_lesson(lesson_name)

    def insert_test_data(self):
        """Вставить тестовые данные"""
        return self.db.test_data()

    def clear_database(self):
        """Очистить БД"""
        return self.db.clear()

    def main_frame_reset(self, only_combobox_values=False):
        """Сбросить главный фрейм"""
        if self.view:
            self.view.main_frame_reset(only_combobox_values)

