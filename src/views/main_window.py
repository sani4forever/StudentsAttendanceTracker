import tkinter as tk
from calendar import monthrange
from tkinter import ttk
from datetime import datetime
import platform
from tkinter.messagebox import showerror, showinfo

from src.views.components.spreadsheet import CustomSpreadsheet
from src.utils.i18n import _  # noqa
from src.utils.logger import setup_logger

logger = setup_logger()
sys_multiplier = 1.3 if platform.system() == "Darwin" else 1
today = datetime.now()


class MainWindow:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.geometry("1000x500")

        self.root.title(_("app_title"))

        self.spreadsheet = None

        self._setup_menu()
        self._setup_main_frame()

    def _setup_menu(self):
        self.main_menu = tk.Menu(self.root)
        self.root.config(menu=self.main_menu)

        # --- МЕНЮ ФАЙЛ ---
        file_menu = tk.Menu(self.main_menu, tearoff=0)
        file_menu.add_command(label=_("Сохранить"), command=self.controller.save_data)
        file_menu.add_command(label=_("Экспорт"), command=self.controller.export_json)
        file_menu.add_separator()
        file_menu.add_command(label=_("Назад"), command=self.root.quit)
        self.main_menu.add_cascade(label=_("Файл"), menu=file_menu)

        # --- МЕНЮ ДОБАВИТЬ ---
        add_menu = tk.Menu(self.main_menu, tearoff=0)
        add_menu.add_command(label="Дату", command=lambda: self.date_window("Добавить"))
        add_menu.add_command(label="Группу", command=lambda: self.group_window("Добавить"))
        add_menu.add_command(label="Студента", command=lambda: self.student_window("Добавить"))
        add_menu.add_command(label="Лекцию", command=lambda: self.lesson_window("Добавить"))
        self.main_menu.add_cascade(label="Добавить", menu=add_menu)

        # --- МЕНЮ ИЗМЕНИТЬ ---
        edit_menu = tk.Menu(self.main_menu, tearoff=0)
        edit_menu.add_command(label="Дату", command=lambda: self.date_window("Изменить"))
        edit_menu.add_command(label="Группу", command=lambda: self.group_window("Изменить"))
        edit_menu.add_command(label="Студента", command=lambda: self.student_window("Изменить"))
        self.main_menu.add_cascade(label="Изменить", menu=edit_menu)

        # --- МЕНЮ УДАЛИТЬ ---
        delete_menu = tk.Menu(self.main_menu, tearoff=0)
        delete_menu.add_command(label="Дату", command=lambda: self.date_window("Удалить"))
        delete_menu.add_command(label="Группу", command=lambda: self.group_window("Удалить"))
        self.main_menu.add_cascade(label="Удалить", menu=delete_menu)

        # --- МЕНЮ СПРАВКА ---
        help_menu = tk.Menu(self.main_menu, tearoff=0)
        help_menu.add_command(label="Об авторе", command=self.about_author)
        help_menu.add_command(label="О программе", command=self.about_window)
        self.main_menu.add_cascade(label="Справка", menu=help_menu)

    def confirmation_window(self, main_window, yes_command, text: str = "Вы уверены?"):  # noqa
        confirm_window = tk.Toplevel(main_window)
        confirm_window.title("Подтверждение")
        confirm_window.geometry("300x100")
        confirm_window.resizable(False, False)
        tk.Label(confirm_window, text=text).pack()
        confirmation_grid = tk.Frame(confirm_window)
        tk.Button(confirmation_grid, text="Да", command=lambda: (yes_command(confirm_window), self.main_frame_reset())).grid(row=0, column=0)
        tk.Button(confirmation_grid, text="Нет", command=confirm_window.destroy).grid(row=0, column=1)
        confirmation_grid.pack()

    def date_window(self, action: str):  # noqa
        window = tk.Toplevel(self.root)
        window.title(f"{action} дату")
        window.geometry("360x170")
        window.resizable(False, False)
        frame = tk.Frame(window)

        info_label = tk.Label(frame, height=2, text="")
        info_label.grid(row=2, column=0, columnspan=2, pady=3.5)
        tk.Button(frame, text=action, command=lambda: (button_press(action), self.main_frame_reset(only_combobox_values=True))).grid(row=3, column=0, columnspan=2, pady=5)

        def year_validate(new_value: str):
            if not new_value:
                return True
            if not new_value.isdigit():
                return False
            return True

        def old_month_postcommand():
            if old_year.get():
                old_month["values"] = self._get_date("month", old_year.get())
            else:
                old_month["values"] = []

        def button_press(_action: str):
            if _action == "Добавить":
                year = new_year.get()
                month = new_month.get()
                month = f"0{month}" if int(month) < 10 else month

                if not year:
                    info_label["text"] = "Внимание:\nНе введён год"
                    return

                is_empty = not bool(self.controller.db.select_where("Dates", ["date"], {"date": f"{year}-{month}"}))

                if not is_empty:
                    info_label["text"] = "Внимание:\nТакая дата уже присутствует в журнале"
                    return

                days = [i for i in range(1, monthrange(int(year), int(month))[1] + 1)]
                for day in days:
                    day = f"0{day}" if day < 10 else day
                    self.controller.db.insert_date(year, month, day, autocommit=False)
                self.db._db.commit()  # noqa

                info_label["text"] = "Успешно добавлено"

            if _action == "Изменить":
                def confirmation_window_yes(confirm_window):
                    _old_days = self._get_date("day", o_year, o_month)
                    _new_days = [i for i in range(1, monthrange(int(n_year), int(n_month))[1] + 1)]
                    if len(_old_days) < len(_new_days):
                        for _day in _new_days[len(_old_days):]:
                            self.controller.db.insert_date(o_year, o_month, _day)
                    for _day in _new_days:
                        _day = f"0{_day}" if _day < 10 else _day
                        self.controller.db.update_date(o_year, o_month, _day,
                                            n_year, n_month, _day,
                                            autocommit=False)
                    self.db._db.commit()  # noqa
                    is_has_old = self.controller.db.select_where("Dates", ["date"], {"date": o_date})
                    if is_has_old:
                        for i in is_has_old:
                            j = i[0].split("-")
                            self.controller.db.delete_date(j[0], j[1], j[2], autocommit=False)
                        self.db._db.commit()  # noqa

                    confirm_window.destroy()
                    info_label["text"] = "Успешно изменено"

                n_year = new_year.get()
                n_month = new_month.get()
                n_month = f"0{n_month}" if int(n_month) < 10 else n_month
                n_date = f"{n_year}-{n_month}"
                o_year = old_year.get()
                o_month = old_month.get()
                o_date = f"{o_year}-{o_month}"

                if not o_year:
                    info_label["text"] = "Внимание:\nНе выбран \"старый\" год"
                    return
                if not o_month:
                    info_label["text"] = "Внимание:\nНе выбран \"старый\" месяц"
                    return
                if not n_year:
                    info_label["text"] = "Внимание:\nНе введён \"новый\" год"
                    return
                if n_date == o_date:
                    info_label["text"] = "Внимание:\nСтарая и новая даты совпадают"
                    return

                is_has_new = bool(self.controller.db.select_where("Dates", ["date"], {"date": n_date}))
                is_has_not_old = not bool(self.controller.db.select_where("Dates", ["date"], {"date": o_date}))

                if is_has_new:
                    info_label["text"] = "Внимание:\nТакая дата уже присутствует в журнале"
                    return
                if is_has_not_old:
                    info_label["text"] = "Внимание:\nТакой даты нет в журнале"
                    return

                confirmation_text = ("Вы уверены?\n"
                                     "Внимание:\n"
                                     "Если в выбранном вами новом году и месяце будет\n"
                                     "меньше или больше дней, чем в предыдущих, то\n"
                                     "несколько последних дней будут удалены или\n"
                                     "добавлены соответственно.")
                self.confirmation_window(window, confirmation_window_yes, confirmation_text)

            if _action == "Удалить":
                def confirmation_window_yes(confirm_window):
                    for i in self.controller.db.select_where("Dates", ["date"], {"date": f"{year}-{month}"}):
                        j = i[0].split("-")
                        self.controller.db.delete_date(j[0], j[1], j[2], autocommit=False)
                    self.db._db.commit()  # noqa
                    confirm_window.destroy()
                    info_label["text"] = "Успешно изменено"

                year = old_year.get()
                month = old_month.get()
                month = f"0{month}" if int(month) < 10 else month

                if not year:
                    info_label["text"] = "Внимание:\nНе выбран год"
                    return
                if not month:
                    info_label["text"] = "Внимание:\nНе выбран месяц"
                    return

                is_has_not_old = not bool(self.controller.db.select_where("Dates", ["date"], {"date": f"{year}-{month}"}))

                if is_has_not_old:
                    info_label["text"] = "Внимание:\nТакой даты нет в журнале"
                    return

                self.confirmation_window(window, confirmation_window_yes)

        if action in ("Добавить", "Изменить"):
            new_date = tk.Frame(frame)

            new_date_enter_label = tk.Label(new_date, text="Выберите дату:", justify="center", width=36)
            new_date_enter_label.grid(row=0, column=0, columnspan=2)

            tk.Label(new_date, text="Год").grid(row=1, column=0)
            tk.Label(new_date, text="Месяц").grid(row=1, column=1)

            new_year = tk.Entry(new_date, width=10, validate="key",
                                validatecommand=(new_date.register(year_validate), "%P"))
            new_month = ttk.Combobox(
                new_date, width=8, state="readonly",
                values=[str(i) for i in range(1, 13)])

            new_year.insert(0, str(today.year))
            new_month.set(str(f"0{today.month}" if today.month < 10 else today.month))

            new_year.grid(row=2, column=0)
            new_month.grid(row=2, column=1)

            new_date.grid(row=0, column=0)

        if action in ("Изменить", "Удалить"):
            if action == "Изменить":
                window.geometry("400x240")
                new_date_enter_label["text"] = "Выберите новую дату:"  # noqa
                new_date.grid(row=1, column=0)  # noqa

            old_date = tk.Frame(frame)

            tk.Label(
                old_date,
                text="Выберите старую дату:" if action == "Изменить" else "Выберите дату:",
                justify="center",
                width=36
            ).grid(row=0, column=0, columnspan=2)

            tk.Label(old_date, text="Год").grid(row=1, column=0)
            tk.Label(old_date, text="Месяц").grid(row=1, column=1)

            old_year = ttk.Combobox(
                old_date, width=8, state="readonly",
                values=self._get_date())
            old_year.bind("<<ComboboxSelected>>", lambda _: old_month.set(""))
            old_month = ttk.Combobox(
                old_date, width=8, state="readonly",
                postcommand=old_month_postcommand)

            old_year.grid(row=2, column=0)
            old_month.grid(row=2, column=1)

            old_date.grid(row=0, column=0)

        frame.pack()

    def group_window(self, action: str):  # noqa
        window_geometry_x = f"{int(300 * sys_multiplier)}"
        window = tk.Toplevel(self.root)
        window.title(f"{action} группу")
        window.geometry(f"{window_geometry_x}x140")
        window.resizable(False, False)
        frame = tk.Frame(window)

        def combobox_postcommand():
            temp = old_group.get().lower()
            if temp:
                old_group["values"] = [i for i in groups if i.lower().startswith(temp)]
            else:
                old_group["values"] = groups

        def button_press(_action: str):
            if _action == "Добавить":
                temp = group.get()
                if not temp:
                    info_label["text"] = "Внимание:\nПустая строка"
                    return
                is_added = self.controller.db.insert_group(temp)
                if not is_added:
                    info_label["text"] = "Внимание:\n Такая группа уже существует"
                    return
                info_label["text"] = " Успешно добавлено"
            if _action == "Изменить":
                temp = old_group.get()
                temp2 = group.get()
                if not temp or not temp2:
                    info_label["text"] = "Внимание:\nПустой выбор или пустая строка"
                    return
                if temp2 == temp:
                    info_label["text"] = "Внимание:\nСтарое и новое имя совпадают"
                    return
                if temp not in groups:
                    info_label["text"] = "Внимание:\nТакая группа не существует"
                    return
                if temp2 in groups:
                    info_label["text"] = "Внимание:\nТакая группа уже существует"
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.update_group(temp, temp2)
                    confirm_window.destroy()
                    info_label["text"] = "Успешно изменено"
                    groups[groups.index(temp)] = temp2
                    old_group.set(temp2)
                    old_group["values"] = groups

                self.confirmation_window(window, confirmation_window_yes)
            if _action == "Удалить":
                temp2 = old_group.get()
                if not temp2:
                    info_label["text"] = "Внимание:\nПустой выбор"
                    return
                if temp2 not in groups:
                    info_label["text"] = "Внимание:\n Такая группа не существует"
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.delete_group(temp2)
                    confirm_window.destroy()
                    info_label["text"] = "Успешно удалено"
                    del groups[groups.index(temp2)]
                    old_group.set("")
                    old_group["values"] = groups

                self.confirmation_window(window, confirmation_window_yes)

        if action in ("Добавить", "Изменить"):
            group_label = tk.Label(frame, text="Группа")
            group_label.grid(row=0, column=0, columnspan=2)
            group = ttk.Entry(frame, width=16)
            group.grid(row=1, column=0, columnspan=2)

        if action in ("Изменить", "Удалить"):
            if action == "Изменить":
                group_label["text"] = "Новое имя группы"  # noqa
                group_label.grid(row=0, column=1, columnspan=1, padx=10)
                group.grid(row=1, column=1, columnspan=1, padx=10)  # noqa
            columnspan = 2 if action == "Удалить" else 1
            tk.Label(frame, text="Старое имя группы").grid(row=0, column=0, columnspan=columnspan, padx=10)

            groups = [g[0] for g in self.controller.db.having_individual_return("Groups", ["group"], ["group"])]
            old_group = ttk.Combobox(
                frame,
                width=16,
                values=groups,
                postcommand=combobox_postcommand
            )
            old_group.grid(row=1, column=0, columnspan=columnspan, padx=10)

        info_label = tk.Label(frame, height=2, text="")
        info_label.grid(row=2, column=0, columnspan=2, pady=3.5)
        tk.Button(frame, text=action, command=lambda: button_press(action)).grid(row=3, column=0, columnspan=2, pady=5)

        frame.pack()

    def student_window(self, action: str):  # noqa
        window_geometry_x = f"{int(860 * sys_multiplier)}"
        window = tk.Toplevel(self.root)
        window.title(f"{action} студента")
        window.geometry(f"{window_geometry_x}x170")
        window.resizable(False, False)
        frame = tk.Frame(window)

        students = self.controller.db.having_individual_return(
            "Students",
            ["group", "surname", "name", "patronymic"],
            ["group", "surname", "name", "patronymic"])

        def combobox_postcommand(combobox_name: str, _new_group: bool = False):
            if _new_group:
                temp_group = new_group.get().lower()
                if temp_group:
                    new_group["values"] = [i for i in groups if i.lower().startswith(temp_group)]
                else:
                    new_group["values"] = groups
                return
            temp_group = old_group.get().lower()
            temp_surname = old_surname.get().lower()
            temp_name = old_name.get().lower()
            temp_patronymic = old_patronymic.get().lower()
            if combobox_name == "group":
                if temp_group:
                    old_group["values"] = [i for i in groups if i.lower().startswith(temp_group)]
                else:
                    old_group["values"] = groups
            if combobox_name == "surname":
                if temp_group:
                    old_surname["values"] = sorted({s[1] for s in students if s[0] == old_group.get() and s[1].lower().startswith(temp_surname)})
                else:
                    old_surname["values"] = []
            if combobox_name == "name":
                if temp_surname:
                    old_name["values"] = sorted({s[2] for s in students if s[0] == old_group.get() and s[1] == old_surname.get() and s[2].lower().startswith(temp_name)})
                else:
                    old_name["values"] = []
            if combobox_name == "patronymic":
                if temp_name:
                    old_patronymic["values"] = sorted(
                        {s[3] for s in students if s[0] == old_group.get() and s[1] == old_surname.get() and s[2] == old_name.get() and s[3].lower().startswith(temp_patronymic)})
                else:
                    old_patronymic["values"] = []

        def old_selected(event):  # noqa
            group_selection = old_group.get()
            surname_selection = old_surname.get()
            name_selection = old_name.get()
            patronymic_selection = old_patronymic.get()

            new_surname.delete(0, tk.END)
            new_name.delete(0, tk.END)
            new_patronymic.delete(0, tk.END)

            new_group.set(group_selection)
            new_surname.insert(0, surname_selection)
            new_name.insert(0, name_selection)
            new_patronymic.insert(0, patronymic_selection)

        def button_press(_action: str):
            if _action == "Добавить":
                temp_group = new_group.get()
                temp_surname = new_surname.get()
                temp_name = new_name.get()
                temp_patronymic = new_patronymic.get()
                if not temp_group:
                    info_label["text"] = "Внимание:\nНе выбрана группа"
                    return
                if not temp_surname or not temp_name or not temp_patronymic:
                    info_label["text"] = "Внимание:\nОдна или несколько строк пусты"
                    return
                is_added = self.controller.db.insert_student(temp_group, temp_surname, temp_name, temp_patronymic)
                if not is_added:
                    info_label["text"] = "Внимание:\n Такой студент в этой группе уже существует"
                    return
                info_label["text"] = " Успешно добавлено"
            if _action == "Изменить":
                temp_old_group = old_group.get()
                temp_old_surname = old_surname.get()
                temp_old_name = old_name.get()
                temp_old_patronymic = old_patronymic.get()
                temp_new_group = new_group.get()
                temp_new_surname = new_surname.get()
                temp_new_name = new_name.get()
                temp_new_patronymic = new_patronymic.get()
                temp_old_student = (temp_old_group, temp_old_surname, temp_old_name, temp_old_patronymic)
                temp_new_student = (temp_new_group, temp_new_surname, temp_new_name, temp_new_patronymic)
                if not temp_old_group:
                    info_label["text"] = "Внимание:\nНе выбрана \"старая\" группа"
                    return
                if not temp_new_group:
                    info_label["text"] = "Внимание:\nНе выбрана \"новая\" группа"
                    return
                if not all(temp_old_student):
                    info_label["text"] = "Внимание:\nОдин или несколько пустых выборов в \"Старом студенте\""
                    return
                if not all(temp_new_student):
                    info_label["text"] = "Внимание:\nОдин или несколько пустых строк в \"Новом студенте\""
                    return
                if temp_old_student == temp_new_student:
                    info_label["text"] = "Внимание:\nСтарые и новые строки студента совпадают"
                    return
                if temp_old_student not in students:
                    info_label["text"] = "Внимание:\nТакого студента в этой группе не существует"
                    return
                if temp_new_student in students:
                    info_label["text"] = "Внимание:\nТакой студент в этой группе уже существует"
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.update_student(*temp_old_student, *temp_new_student)
                    confirm_window.destroy()
                    info_label["text"] = "Успешно изменено"
                    students[students.index(temp_old_student)] = temp_new_student
                    old_surname.set(temp_new_surname)
                    old_name.set(temp_new_name)
                    old_patronymic.set(temp_new_patronymic)

                self.confirmation_window(window, confirmation_window_yes)
            if _action == "Удалить":
                temp_group = old_group.get()
                temp_surname = old_surname.get()
                temp_name = old_name.get()
                temp_patronymic = old_patronymic.get()
                temp_student = (temp_group, temp_surname, temp_name, temp_patronymic)
                if not temp_group:
                    info_label["text"] = "Внимание:\nНе выбрана группа"
                    return
                if not all(temp_student):
                    info_label["text"] = "Внимание:\nОдин или несколько пустых выборов в \"Старом студенте\""
                    return
                if temp_student not in students:
                    info_label["text"] = "Внимание:\nТакого студента в этой группе не существует"
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.delete_student(*temp_student)
                    confirm_window.destroy()
                    info_label["text"] = "Успешно удалено"
                    del students[students.index(temp_student)]
                    old_group.set("")
                    old_surname.set("")
                    old_name.set("")
                    old_patronymic.set("")

                self.confirmation_window(window, confirmation_window_yes)

        if action in ("Добавить", "Изменить"):
            new_student = tk.Frame(frame)
            new_student_label = tk.Label(new_student, text="Новый студент:")
            new_student_label.grid(row=0, column=0, columnspan=4)

            new_group_label = tk.Label(new_student, text="Группа")
            new_surname_label = tk.Label(new_student, text="Фамилия")
            new_name_label = tk.Label(new_student, text="Имя")
            new_patronymic_label = tk.Label(new_student, text="Отчество")

            groups = sorted({s[0] for s in students})
            new_group = ttk.Combobox(
                new_student,
                width=26,
                values=groups,
                postcommand=lambda: combobox_postcommand("group", True)
            )
            new_surname = ttk.Entry(new_student, width=28)
            new_name = ttk.Entry(new_student, width=28)
            new_patronymic = ttk.Entry(new_student, width=28)

            new_group_label.grid(row=1, column=0)
            new_surname_label.grid(row=1, column=1)
            new_name_label.grid(row=1, column=2)
            new_patronymic_label.grid(row=1, column=3)

            new_group.grid(row=2, column=0)
            new_surname.grid(row=2, column=1)
            new_name.grid(row=2, column=2)
            new_patronymic.grid(row=2, column=3)

            new_student.grid(row=0, column=0)

        if action in ("Изменить", "Удалить"):
            if action == "Изменить":
                window.geometry(f"{window_geometry_x}x260")
                new_student.grid(row=1, column=0, pady=10)  # noqa

            old_student = tk.Frame(frame)
            old_student_label = tk.Label(old_student, text="Старый студент:")
            old_student_label.grid(row=0, column=0, columnspan=4)

            old_group_label = tk.Label(old_student, text="Группа")
            old_surname_label = tk.Label(old_student, text="Фамилия")
            old_name_label = tk.Label(old_student, text="Имя")
            old_patronymic_label = tk.Label(old_student, text="Отчество")

            groups = sorted({s[0] for s in students})
            old_group = ttk.Combobox(
                old_student,
                width=26,
                values=groups,
                postcommand=lambda: combobox_postcommand("group")
            )
            old_surname = ttk.Combobox(
                old_student,
                width=26,
                values=[],
                postcommand=lambda: combobox_postcommand("surname")
            )
            old_name = ttk.Combobox(
                old_student,
                width=26,
                values=[],
                postcommand=lambda: combobox_postcommand("name")
            )
            old_patronymic = ttk.Combobox(
                old_student,
                width=26,
                values=[],
                postcommand=lambda: combobox_postcommand("patronymic")
            )
            if action == "Изменить":
                old_group.bind("<<ComboboxSelected>>", old_selected)
                old_surname.bind("<<ComboboxSelected>>", old_selected)
                old_name.bind("<<ComboboxSelected>>", old_selected)
                old_patronymic.bind("<<ComboboxSelected>>", old_selected)

            old_group_label.grid(row=1, column=0)
            old_surname_label.grid(row=1, column=1)
            old_name_label.grid(row=1, column=2)
            old_patronymic_label.grid(row=1, column=3)

            old_group.grid(row=2, column=0)
            old_surname.grid(row=2, column=1)
            old_name.grid(row=2, column=2)
            old_patronymic.grid(row=2, column=3)

            old_student.grid(row=0, column=0)

        info_label = tk.Label(frame, height=2, text="")
        info_label.grid(row=2, column=0, columnspan=2, pady=3.5)
        tk.Button(frame, text=action, command=lambda: button_press(action)).grid(row=3, column=0, columnspan=2, pady=5)

        frame.pack()

    def lesson_window(self, action: str):  # noqa
        window_geometry_x = f"{int(500 * sys_multiplier)}"
        window = tk.Toplevel(self.root)
        window.title(f"{action} лекцию/занятие")
        window.geometry(f"{window_geometry_x}x140")
        window.resizable(False, False)
        frame = tk.Frame(window)

        def combobox_postcommand():
            temp = old_lesson.get().lower()
            if temp:
                old_lesson["values"] = [i for i in lessons if i.lower().startswith(temp)]
            else:
                old_lesson["values"] = lessons

        def button_press(_action: str):
            if _action == "Добавить":
                temp = lesson.get()
                if not temp:
                    info_label["text"] = "Внимание:\nПустая строка"
                    return
                is_added = self.controller.db.insert_lesson(temp)
                if not is_added:
                    info_label["text"] = "Внимание:\n Такая лекция уже существует"
                    return
                info_label["text"] = " Успешно добавлено"
            if _action == "Изменить":
                temp = old_lesson.get()
                temp2 = lesson.get()
                if not temp or not temp2:
                    info_label["text"] = "Внимание:\nПустой выбор или пустая строка"
                    return
                if temp2 == temp:
                    info_label["text"] = "Внимание:\nСтарое и новое имя совпадают"
                    return
                if temp not in lessons:
                    info_label["text"] = "Внимание:\nТакая лекция не существует"
                    return
                if temp2 in lessons:
                    info_label["text"] = "Внимание:\nТакая лекция уже существует"
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.update_lesson(temp, temp2)
                    confirm_window.destroy()
                    info_label["text"] = "Успешно изменено"
                    lessons[lessons.index(temp)] = temp2
                    old_lesson.set(temp2)
                    old_lesson["values"] = lessons

                self.confirmation_window(window, confirmation_window_yes)
            if _action == "Удалить":
                temp2 = old_lesson.get()
                if not temp2:
                    info_label["text"] = "Внимание:\nПустой выбор"
                    return
                if temp2 not in lessons:
                    info_label["text"] = "Внимание:\n Такая лекция не существует"
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.delete_lesson(temp2)
                    confirm_window.destroy()
                    info_label["text"] = "Успешно удалено"
                    del lessons[lessons.index(temp2)]
                    old_lesson.set("")
                    old_lesson["values"] = lessons

                self.confirmation_window(window, confirmation_window_yes)

        if action in ("Добавить", "Изменить"):
            lesson_label = tk.Label(frame, text="Лекция/занятие")
            lesson_label.grid(row=0, column=0, columnspan=2)
            lesson = ttk.Entry(frame, width=30)
            lesson.grid(row=1, column=0, columnspan=2)

        if action in ("Изменить", "Удалить"):
            if action == "Изменить":
                lesson_label["text"] = "Новое имя лекции"  # noqa
                lesson_label.grid(row=0, column=1, columnspan=1, padx=10)
                lesson.grid(row=1, column=1, columnspan=1, padx=10)  # noqa
            columnspan = 2 if action == "Удалить" else 1
            tk.Label(frame, text="Старое имя лекции").grid(row=0, column=0, columnspan=columnspan, padx=10)

            lessons = [le[0] for le in self.controller.db.having_individual_return("Lessons", ["lesson"], ["lesson"])]
            old_lesson = ttk.Combobox(
                frame,
                width=30,
                values=lessons,
                postcommand=combobox_postcommand
            )
            old_lesson.grid(row=1, column=0, columnspan=columnspan, padx=10)

        info_label = tk.Label(frame, height=2, text="")
        info_label.grid(row=2, column=0, columnspan=2, pady=3.5)
        tk.Button(frame, text=action, command=lambda: button_press(action)).grid(row=3, column=0, columnspan=2, pady=5)

        frame.pack()


    def about_window(self):  # noqa
        about = tk.Toplevel(self.root)
        about.title("О программе")
        about.geometry("600x550")  # Увеличиваем размер окна для удобства
        about.resizable(False, False)

        # Фрейм для содержимого
        content_frame = tk.Frame(about, padx=10, pady=10)
        content_frame.pack(expand=True, fill="both")

        # Попытка загрузить изображение (если оно есть)
        try:
            photo = tk.PhotoImage(file="src/resources/images/program.png")  # Указываем путь к изображению

            # Добавляем изображение в окно
            img_label = tk.Label(content_frame, image=photo)
            img_label.image = photo  # Сохраняем ссылку на объект изображения
            img_label.pack(pady=(5, 10))
        except Exception as e:
            tk.Label(content_frame, text=f"Ошибка загрузки изображения: {e}", fg="red").pack()

        # Информация о программе
        tk.Label(content_frame, text="Приложение: Учет посещаемости лекционных занятий",
                 font=("Arial", 12, "bold")).pack()
        tk.Label(content_frame, text="Программа позволяет:", font=("Arial", 12)).pack()
        tk.Label(content_frame, text="1. Добавлять посещения по дате.", font=("Arial", 12)).pack()
        tk.Label(content_frame, text="2. Отображать список студентов, посещавших занятия на определенную дату.",
                 font=("Arial", 12)).pack()
        tk.Label(content_frame, text="3. Добавлять и удалять группы.", font=("Arial", 12)).pack()
        tk.Label(content_frame, text="4. Сортировать по количеству посещений и по фамилии студентов.",
                 font=("Arial", 12)).pack()

        tk.Label(content_frame, text="Версия ver.1337",
                 font=("Arial", 12)).pack()

        # Кнопка "Закрыть окно"
        tk.Button(content_frame, text="Закрыть окно", command=about.destroy, font=("Arial", 10)).pack(pady=10)

    def about_author(self):  # noqa
        # Создаем окно
        about = tk.Toplevel(self.root)
        about.title("Об авторе")
        about.geometry("300x600")
        about.resizable(False, False)

        # Фрейм для содержимого
        content_frame = tk.Frame(about, padx=10, pady=10)
        content_frame.pack(expand=True, fill="both")

        # Добавление изображения
        try:
            # Загружаем изображение (с предварительно вручную сделанным масштабом)
            photo = tk.PhotoImage(file="src/resources/images/authorImage.png")  # Укажите путь к вашему изображению

            # Добавляем изображение в окно
            img_label = tk.Label(content_frame, image=photo)
            img_label.image = photo  # Сохраняем ссылку на объект изображения
            img_label.pack(pady=(5, 10))
        except Exception as e:
            tk.Label(content_frame, text=f"Ошибка загрузки изображения: {e}", fg="red").pack()

        # Информация об авторе
        tk.Label(content_frame, text="Автор", font=("Arial", 14, "bold")).pack()
        tk.Label(content_frame, text="студент группы 10701123", font=("Arial", 12)).pack()
        tk.Label(content_frame, text="Гошко Александр Игоревич", font=("Arial", 12)).pack()
        tk.Label(content_frame, text="sani4forever@gmail.com", font=("Arial", 12), fg="blue").pack(pady=(0, 10))

        # Кнопка "Назад"
        tk.Button(content_frame, text="Назад", command=about.destroy, font=("Arial", 10)).pack(pady=10)

    def test_data_window(self):
        def yes_command():
            self.controller.db.test_data()
            test_data.destroy()

        test_data = tk.Toplevel(self.root)
        test_data.title("Вставка тестовых данных")
        test_data.geometry("250x100")
        test_data.resizable(False, False)

        tk.Label(test_data, text="Вы уверенны, что хотите").pack()
        tk.Label(test_data, text="вставить тестовые данные?").pack()
        tk.Label(test_data, text="(4500 записей)").pack()
        test_data_grid = tk.Frame(test_data)
        tk.Button(test_data_grid, text="Нет", command=test_data.destroy).grid(row=0, column=0)
        tk.Button(test_data_grid, text="Да", command=yes_command).grid(row=0, column=1)
        test_data_grid.pack()

    def db_clear_window(self):
        def yes_command():
            self.controller.db.clear()
            clear.destroy()

        clear = tk.Toplevel(self.root)
        clear.title("Очистка БД")
        clear.geometry("200x80")
        clear.resizable(False, False)

        tk.Label(clear, text="Вы уверенны, что хотите").pack()
        tk.Label(clear, text="очистить базу данных?").pack()
        clear_grid = tk.Frame(clear)
        tk.Button(clear_grid, text="Нет", command=clear.destroy).grid(row=0, column=0)
        tk.Button(clear_grid, text="Да", command=yes_command).grid(row=0, column=1)
        clear_grid.pack()

    def close_program(self):
        self.controller.db.close()
        self.root.destroy()

    def _setup_main_frame(self):
        def create_spreadsheet():
            colors = {
                "0": "#9EE2C0",
                "1": "#F5E2B5",
                "2": "#FF8477",
            }

            temp_journal = self.controller.db.select_where(
                "Journal",
                ["date", "group", "surname", "name", "patronymic", "lesson", "missed_hours"],
                {
                    "date": f"{self.year.get()}-{self.month.get()}",
                    "group": self.groups.get(),
                    "lesson": self.lessons.get()
                },
                ["surname", "name", "patronymic", "date"]
            )

            if not temp_journal:
                showerror(title="Ошибка",
                          message="Таких данных нет в базе.\nПожалуйста, выберите другие данные сверху.")
                self.root.focus_set()
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

            self.spreadsheet.create(
                columns=spreadsheet_width,
                rows=spreadsheet_height,
                columns_headers=days,
                rows_headers=students,
                set_values=spreadsheet_set_values,
                cells_values=spreadsheet_cells_values,
                cells_colors=colors
            )

            temp_journal.clear()

        def save_spreadsheet():
            for row_header, row in self.spreadsheet.cells.items():
                for column_header, cell in row.items():
                    new_missed_hours = cell.cget("text")
                    old_date = f"{self.year.get()}-{self.month.get()}-{column_header.split('__')[1]}"
                    old_group = self.groups.get()
                    old_surname = row_header.split("__")[1].split(" ")[0]
                    old_name = row_header.split("__")[1].split(" ")[1]
                    old_patronymic = row_header.split("__")[1].split(" ")[2]
                    old_lesson = self.lessons.get()
                    self.controller.db._db.execute(  # noqa
                        f"""
                    UPDATE "Journal"
                    SET "missed_hours" = "{new_missed_hours}"
                    WHERE "date" = "{old_date}" AND
                        "group" = "{old_group}" AND
                        "surname" = "{old_surname}" AND
                        "name" = "{old_name}" AND
                        "patronymic" = "{old_patronymic}" AND
                        "lesson" = "{old_lesson}"
                    ;""")

            self.controller.db._db.commit()  # noqa
            showinfo(title="Успешно", message="Данные успешно сохранены.")

        def filtering():
            if self.year.get():
                self.month["values"] = [""] + self._get_date("month", self.year.get())
            else:
                self.month.set("")
                self.month["values"] = []
            if all([self.year.get(), self.month.get(), self.groups.get(), self.lessons.get()]):
                self.main_frame_reset(only_spreadsheet=True)
                create_spreadsheet()
            else:
                self.main_frame_reset(only_spreadsheet=True)

        # Header (filtering)
        filtering_frame = tk.Frame(self.root)

        for c in range(4): filtering_frame.columnconfigure(index=c, weight=1)  # noqa
        # Labels
        tk.Label(filtering_frame, text="Год:").grid(row=0, column=0)
        tk.Label(filtering_frame, text="Месяц:").grid(row=0, column=1)
        tk.Label(filtering_frame, text="Группа:").grid(row=0, column=2)
        tk.Label(filtering_frame, text="Предмет:").grid(row=0, column=3)
        # Combo boxes
        self.year = ttk.Combobox(filtering_frame, width=10, state="readonly")
        self.month = ttk.Combobox(filtering_frame, width=10, state="readonly")
        self.groups = ttk.Combobox(filtering_frame, width=10, state="readonly")
        self.lessons = ttk.Combobox(filtering_frame, width=30, state="readonly")
        # Combo boxes bindings
        self.year.bind("<<ComboboxSelected>>", lambda event: filtering())
        self.month.bind("<<ComboboxSelected>>", lambda event: filtering())
        self.groups.bind("<<ComboboxSelected>>", lambda event: filtering())
        self.lessons.bind("<<ComboboxSelected>>", lambda event: filtering())
        # Combo boxes placement
        self.year.grid(row=1, column=0)
        self.month.grid(row=1, column=1)
        self.groups.grid(row=1, column=2)
        self.lessons.grid(row=1, column=3)

        filtering_frame.pack(fill="x", pady=5)

        # Main spreadsheet
        self.spreadsheet = CustomSpreadsheet(self.root)
        self.spreadsheet.pack(fill="both", expand=True)

        bottom = tk.Frame(self.root)
        bottom.pack(side="bottom", fill="x")

        bottom_color_labels = tk.Frame(bottom)
        bottom_color_labels.pack()

        bottom_buttons = tk.Frame(bottom)
        bottom_buttons.pack(side="bottom")

        tk.Button(bottom_buttons, text="Сохранить", command=save_spreadsheet).pack(side="left")
        tk.Button(bottom_buttons, text="Сбросить", command=self.main_frame_reset).pack(side="right")

        color_placeholder = " " * 4
        tk.Label(bottom_color_labels, text=color_placeholder, bg="green").pack(side="left")
        tk.Label(bottom_color_labels, text=" - 0 пропущенных часов, ").pack(side="left")
        tk.Label(bottom_color_labels, text=color_placeholder, bg="yellow").pack(side="left")
        tk.Label(bottom_color_labels, text=" - 1 пропущенный час, ").pack(side="left")
        tk.Label(bottom_color_labels, text=color_placeholder, bg="red").pack(side="left")
        tk.Label(bottom_color_labels, text=" - 2 пропущенных часа").pack(side="left")

        self.main_frame_reset()

    def main_frame_reset(self, only_spreadsheet: bool = False, only_combobox_values: bool = False):
        def clear_combobox_values():
            self.year["values"] = [""] + [i for i in self._get_date()]
            self.month["values"] = [""] + [i for i in self._get_date("month", self.year.get())]
            self.groups["values"] = [""] + [i[0] for i in
                                            self.controller.db.having_individual_return("Groups", ["group"], ["group"])]
            self.lessons["values"] = [""] + [i[0] for i in
                                             self.controller.db.having_individual_return("Lessons", ["lesson"], ["lesson"])]

        if only_combobox_values:
            clear_combobox_values()
            return
        self.spreadsheet.clear()
        if only_spreadsheet:
            return
        self.year.set(today.year)
        self.month.set(f"0{today.month}" if today.month < 10 else today.month)
        self.groups.set("")
        self.lessons.set("")
        clear_combobox_values()

    def start(self):
        self.root.mainloop()

    def _get_date(self, select_type: str = "year", year: str = None, month: str = None):
        command_select = 'SELECT DISTINCT strftime("%Y", "date") AS "year"'
        command_where = ""
        command_order = ' ORDER BY "year"'
        if select_type == "month" or select_type == "day":
            command_select += ', strftime("%m", "date") AS "month"'
            command_where += f' WHERE "year" IS "{year}"'
            command_order += ', "month"'
        if select_type == "day":
            command_select += ', strftime("%d", "date") AS "day"'
            command_where += f' AND "month" IS "{month}"'
            command_order += ', "day"'
        command = f'{command_select} FROM "Dates" {command_where} {command_order};'
        cursor = self.controller.db._db.cursor()  # noqa
        cursor.execute(command)
        result = cursor.fetchall()
        cursor.close()
        if select_type == "month":
            return [i[1] for i in result]
        if select_type == "day":
            return [i[2] for i in result]
        return [i[0] for i in result]
