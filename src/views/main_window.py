import subprocess
import sys
import tkinter as tk
import os
from calendar import monthrange
from tkinter import ttk
from datetime import datetime
import platform
from tkinter.messagebox import showerror, showinfo

from src.views.components.spreadsheet import CustomSpreadsheet
from src.utils.i18n import _
from src.utils.logger import setup_logger
from tkinter import filedialog

logger = setup_logger()
sys_multiplier = 1.3 if platform.system() == "Darwin" else 1
today = datetime.now()


class MainWindow:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        #self.root.geometry("1000x500")

        self.root.title(_("app_title"))

        self.spreadsheet = None

        self._setup_menu()
        self._setup_main_frame()

    def _setup_menu(self):
        self.main_menu = tk.Menu(self.root)
        self.root.config(menu=self.main_menu)

        # --- FILE MENU ---
        file_menu = tk.Menu(self.main_menu, tearoff=0)
        file_menu.add_command(label=_("btn_save"), command=self.controller.save_data)
        file_menu.add_separator()
        file_menu.add_command(label=_("btn_back"), command=self.root.quit)
        self.main_menu.add_cascade(label=_("menu_file"), menu=file_menu)

        # --- IMPORT MENU ---
        import_menu = tk.Menu(self.main_menu, tearoff=0)

        import_menu.add_command(
            label=_("title_automatic_import"),
            command=self.open_import_file_dialog
        )

        self.main_menu.add_cascade(label=_("title_import"), menu=import_menu)

        # --- EXPORT MENU ---
        export_menu = tk.Menu(self.main_menu, tearoff=0)

        # JSON Export
        export_menu.add_command(
            label=_("title_export_json"),
            command=self.controller.export_json
        )
        export_menu.add_separator()

        # XML Export Submenu
        xml_export_menu = tk.Menu(export_menu, tearoff=0)
        xml_export_menu.add_command(
            label=_("title_export_xml_groups"),
            command=self.controller.export_xml_groups
        )
        xml_export_menu.add_command(
            label=_("title_export_xml_students"),
            command=self.controller.export_xml_students
        )
        xml_export_menu.add_command(
            label=_("title_export_xml_journal"),
            command=self.controller.export_xml_journal
        )
        export_menu.add_cascade(
            label=_("title_export_xml"),
            menu=xml_export_menu
        )

        # Binary Export Submenu
        binary_export_menu = tk.Menu(export_menu, tearoff=0)
        binary_export_menu.add_command(
            label=_("title_export_pickle"),
            command=self.controller.export_pickle
        )
        binary_export_menu.add_command(
            label=_("title_export_msgpack"),
            command=self.controller.export_msgpack
        )
        export_menu.add_cascade(
            label=_("title_export_binary"),
            menu=binary_export_menu
        )

        self.main_menu.add_cascade(label=_("title_export"), menu=export_menu)

        # --- ADD MENU ---
        add_menu = tk.Menu(self.main_menu, tearoff=0)
        add_menu.add_command(label=_("title_add_date"), command=lambda: self.date_window(_("btn_add")))
        add_menu.add_command(label=_("title_add_group"), command=lambda: self.group_window(_("btn_add")))
        add_menu.add_command(label=_("title_add_student"), command=lambda: self.student_window(_("btn_add")))
        add_menu.add_command(label=_("title_add_lesson"), command=lambda: self.lesson_window(_("btn_add")))
        self.main_menu.add_cascade(label=_("btn_add"), menu=add_menu)

        # --- EDIT MENU ---
        edit_menu = tk.Menu(self.main_menu, tearoff=0)
        edit_menu.add_command(label=_("title_edit_date"), command=lambda: self.date_window(_("btn_edit")))
        edit_menu.add_command(label=_("title_edit_group"), command=lambda: self.group_window(_("btn_edit")))
        edit_menu.add_command(label=_("title_edit_student"), command=lambda: self.student_window(_("btn_edit")))
        edit_menu.add_command(label=_("title_edit_lesson"), command=lambda: self.lesson_window(_("btn_edit")))
        self.main_menu.add_cascade(label=_("menu_edit"), menu=edit_menu)

        # --- DELETE MENU ---
        delete_menu = tk.Menu(self.main_menu, tearoff=0)
        delete_menu.add_command(label=_("title_delete_date"), command=lambda: self.date_window(_("btn_delete")))
        delete_menu.add_command(label=_("title_delete_group"), command=lambda: self.group_window(_("btn_delete")))
        delete_menu.add_command(label=_("title_delete_student"), command=lambda: self.student_window(_("btn_delete")))
        delete_menu.add_command(label=_("title_delete_lesson"), command=lambda: self.lesson_window(_("btn_delete")))
        self.main_menu.add_cascade(label=_("menu_delete"), menu=delete_menu)

        # --- SETTINGS MENU ---

        settings_menu = tk.Menu(self.main_menu, tearoff=0)

        language_menu = tk.Menu(settings_menu, tearoff=0)

        # Переменные для радиокнопок
        self.language_var = tk.StringVar(value=self.controller.get_current_language())

        for lang_code in self.controller.get_available_languages():
            # Получаем название языка из локализации
            lang_name = _("language_russian") if lang_code == "ru" else _("language_english")

            language_menu.add_radiobutton(
                label=lang_name,
                variable=self.language_var,
                value=lang_code,
                command=lambda code=lang_code: self._on_language_changed(code)
            )

        settings_menu.add_cascade(label=_("menu_language"), menu=language_menu)

        self.main_menu.add_cascade(label=_("menu_settings"), menu=settings_menu)

        # --- HELP MENU ---
        help_menu = tk.Menu(self.main_menu, tearoff=0)
        help_menu.add_command(label=_("title_about_author"), command=self.about_author)
        help_menu.add_command(label=_("title_about"), command=self.about_window)

        # --- OTHER MENU ---
        other_menu = tk.Menu(self.main_menu, tearoff=0)
        other_menu.add_command(label=_("menu_test_data"), command=self.test_data_window)
        other_menu.add_command(label=_("menu_clear_db"), command=self.db_clear_window)
        other_menu.add_separator()
        other_menu.add_command(label=_("menu_exit"), command=self.close_program)
        help_menu.add_cascade(label=_("menu_other"), menu=other_menu)

        self.main_menu.add_cascade(label=_("menu_help"), menu=help_menu)

    def _on_language_changed(self, language_code: str):
        """Обработчик изменения языка"""
        # Изменяем язык через контроллер
        success = self.controller.change_language(language_code)

        if success:
            # Обновляем текущий выбор в меню
            self.language_var.set(language_code)

            # Спрашиваем пользователя о перезапуске
            self._ask_for_restart()

    def _ask_for_restart(self):
        """Спросить пользователя о перезапуске приложения"""
        # Создаем отдельное окно для подтверждения
        restart_window = tk.Toplevel(self.root)
        restart_window.title(_("menu_settings"))
        restart_window.geometry("400x150")
        restart_window.resizable(False, False)
        restart_window.transient(self.root)
        restart_window.grab_set()

        # Центрируем окно
        restart_window.update_idletasks()
        width = restart_window.winfo_width()
        height = restart_window.winfo_height()
        x = (restart_window.winfo_screenwidth() // 2) - (width // 2)
        y = (restart_window.winfo_screenheight() // 2) - (height // 2)
        restart_window.geometry(f'{width}x{height}+{x}+{y}')

        # Сообщение
        message = tk.Label(
            restart_window,
            text=_("success_language_changed") + "\n\n" +
                 _("restart_required") + "\n" +
                 _("confirm_restart"),
            justify="center",
            padx=20,
            pady=20
        )
        message.pack()

        # Кнопки
        button_frame = tk.Frame(restart_window)
        button_frame.pack(pady=10)

        def restart_now():
            """Перезапустить приложение сейчас"""
            restart_window.destroy()
            self._restart_application()

        def restart_later():
            """Отложить перезапуск"""
            restart_window.destroy()
            # Просто обновляем заголовок окна
            self.root.title(_("app_title"))

        tk.Button(
            button_frame,
            text=_("btn_yes"),
            command=restart_now,
            width=10
        ).pack(side="left", padx=10)

        tk.Button(
            button_frame,
            text=_("btn_no"),
            command=restart_later,
            width=10
        ).pack(side="left", padx=10)

    def _restart_application(self):
        """Перезапустить приложение"""
        try:
            # Сохраняем текущее состояние
            self.controller.save_current_state()

            # Закрываем текущее окно
            self.root.destroy()

            # Перезапускаем приложение
            python = sys.executable
            subprocess.Popen([python] + sys.argv)

            # Завершаем текущий процесс
            sys.exit(0)

        except Exception as e:
            logger.error(f"Error restarting application: {e}")
            self.controller.show_error(
                _("menu_settings"),
                _("restart_required")
            )

    def confirmation_window(self, main_window, yes_command, text: str = _("confirm_exit")):
        confirm_window = tk.Toplevel(main_window)
        confirm_window.title(_("title_confirm"))
        confirm_window.geometry("300x100")
        confirm_window.resizable(False, False)
        tk.Label(confirm_window, text=text).pack()
        confirmation_grid = tk.Frame(confirm_window)
        tk.Button(confirmation_grid, text=_("btn_yes"),
                  command=lambda: (yes_command(confirm_window), self.main_frame_reset())).grid(row=0, column=0)
        tk.Button(confirmation_grid, text=_("btn_no"),
                  command=confirm_window.destroy).grid(row=0, column=1)
        confirmation_grid.pack()

    def date_window(self, action: str):
        window = tk.Toplevel(self.root)
        if action == _("btn_add"):
            window.title(_("title_add_date"))
        elif action == _("btn_edit"):
            window.title(_("title_edit_date"))
        elif action == _("btn_delete"):
            window.title(_("title_delete_date"))

        window.geometry("360x170")
        window.resizable(False, False)
        frame = tk.Frame(window)

        info_label = tk.Label(frame, height=2, text="")
        info_label.grid(row=2, column=0, columnspan=2, pady=3.5)
        tk.Button(frame, text=action,
                  command=lambda: (button_press(action), self.main_frame_reset(only_combobox_values=True))
                  ).grid(row=3, column=0, columnspan=2, pady=5)

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
            if _action == _("btn_add"):
                year = new_year.get()
                month = new_month.get()
                month = f"0{month}" if int(month) < 10 else month

                if not year:
                    info_label["text"] = _("err_no_year")
                    return

                is_empty = not bool(self.controller.db.select_where("Dates", ["date"], {"date": f"{year}-{month}"}))

                if not is_empty:
                    info_label["text"] = _("err_date_exists")
                    return

                days = [i for i in range(1, monthrange(int(year), int(month))[1] + 1)]
                for day in days:
                    day = f"0{day}" if day < 10 else day
                    self.controller.db.insert_date(year, month, day, autocommit=False)
                self.controller.db._db.commit()

                info_label["text"] = _("success_added")

            if _action == _("btn_edit"):
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
                    self.controller.db._db.commit()
                    is_has_old = self.controller.db.select_where("Dates", ["date"], {"date": o_date})
                    if is_has_old:
                        for i in is_has_old:
                            j = i[0].split("-")
                            self.controller.db.delete_date(j[0], j[1], j[2], autocommit=False)
                        self.controller.db._db.commit()

                    confirm_window.destroy()
                    info_label["text"] = _("success_edited")

                n_year = new_year.get()
                n_month = new_month.get()
                n_month = f"0{n_month}" if int(n_month) < 10 else n_month
                n_date = f"{n_year}-{n_month}"
                o_year = old_year.get()
                o_month = old_month.get()
                o_date = f"{o_year}-{o_month}"

                if not o_year:
                    info_label["text"] = _("err_no_year").replace("выбран", "выбран \"старый\"")
                    return
                if not o_month:
                    info_label["text"] = _("err_no_month").replace("выбран", "выбран \"старый\"")
                    return
                if not n_year:
                    info_label["text"] = _("err_no_year").replace("выбран", "введён \"новый\"")
                    return
                if n_date == o_date:
                    info_label["text"] = _("err_same_values").replace("значение", "даты")
                    return

                is_has_new = bool(self.controller.db.select_where("Dates", ["date"], {"date": n_date}))
                is_has_not_old = not bool(self.controller.db.select_where("Dates", ["date"], {"date": o_date}))

                if is_has_new:
                    info_label["text"] = _("err_date_exists")
                    return
                if is_has_not_old:
                    info_label["text"] = _("err_date_not_exists")
                    return

                confirmation_text = f"{_('confirm_delete')}\n{_('warning_date_change')}"
                self.confirmation_window(window, confirmation_window_yes, confirmation_text)

            if _action == _("btn_delete"):
                def confirmation_window_yes(confirm_window):
                    for i in self.controller.db.select_where("Dates", ["date"], {"date": f"{year}-{month}"}):
                        j = i[0].split("-")
                        self.controller.db.delete_date(j[0], j[1], j[2], autocommit=False)
                    self.controller.db._db.commit()
                    confirm_window.destroy()
                    info_label["text"] = _("success_deleted")

                year = old_year.get()
                month = old_month.get()
                month = f"0{month}" if int(month) < 10 else month

                if not year:
                    info_label["text"] = _("err_no_year")
                    return
                if not month:
                    info_label["text"] = _("err_no_month")
                    return

                is_has_not_old = not bool(
                    self.controller.db.select_where("Dates", ["date"], {"date": f"{year}-{month}"}))

                if is_has_not_old:
                    info_label["text"] = _("err_date_not_exists")
                    return

                self.confirmation_window(window, confirmation_window_yes)

        if action in (_("btn_add"), _("btn_edit")):
            new_date = tk.Frame(frame)

            new_date_enter_label = tk.Label(new_date, text=_("label_select_date"),
                                            justify="center", width=36)
            new_date_enter_label.grid(row=0, column=0, columnspan=2)

            tk.Label(new_date, text=_("label_year")).grid(row=1, column=0)
            tk.Label(new_date, text=_("label_month")).grid(row=1, column=1)

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

        if action in (_("btn_edit"), _("btn_delete")):
            if action == _("btn_edit"):
                window.geometry("400x240")
                new_date_enter_label["text"] = _("label_select_new_date")
                new_date.grid(row=1, column=0)

            old_date = tk.Frame(frame)

            tk.Label(
                old_date,
                text=_("label_select_old_date") if action == _("btn_edit") else _("label_select_date"),
                justify="center",
                width=36
            ).grid(row=0, column=0, columnspan=2)

            tk.Label(old_date, text=_("label_year")).grid(row=1, column=0)
            tk.Label(old_date, text=_("label_month")).grid(row=1, column=1)

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

    def open_import_file_dialog(self):
        filename = filedialog.askopenfilename(
            title="Select file to import",
            filetypes=[
                ("All supported files", "*.json *.xml *.pkl *.pickle *.msgpack"),
                ("JSON files", "*.json"),
                ("XML files", "*.xml"),
                ("Pickle files", "*.pkl *.pickle"),
                ("MessagePack files", "*.msgpack"),
                ("All files", "*.*")
            ]
        )

        if filename:
            # Проверяем существование файла
            if not os.path.exists(filename):
                self.controller.show_error("Import Error", f"Файл не найден: {filename}")
                return

            # Проверяем размер файла
            try:
                file_size = os.path.getsize(filename)
                if file_size > 10 * 1024 * 1024:  # 10 MB
                    confirm = self.controller.ask_confirmation(
                        "Large File",
                        f"Файл очень большой ({file_size / 1024 / 1024:.1f} MB). Продолжить импорт?"
                    )
                    if not confirm:
                        return
            except Exception as e:
                self.controller.show_error("Import Error", f"Не удалось проверить файл: {str(e)}")
                return

            self.controller.auto_detect_and_import(filename)

    def group_window(self, action: str):
        window_geometry_x = f"{int(300 * sys_multiplier)}"
        window = tk.Toplevel(self.root)
        if action == _("btn_add"):
            window.title(_("title_add_group"))
        elif action == _("btn_edit"):
            window.title(_("title_edit_group"))
        elif action == _("btn_delete"):
            window.title(_("title_delete_group"))

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
            if _action == _("btn_add"):
                temp = group.get()
                if not temp:
                    info_label["text"] = _("err_empty_string")
                    return
                is_added = self.controller.db.insert_group(temp)
                if not is_added:
                    info_label["text"] = _("err_group_exists")
                    return
                info_label["text"] = _("success_added")

            if _action == _("btn_edit"):
                temp = old_group.get()
                temp2 = group.get()
                if not temp or not temp2:
                    info_label["text"] = _("err_empty_string") + "\n" + _("err_no_group").replace("выбрана",
                                                                                                  "выбор или строка")
                    return
                if temp2 == temp:
                    info_label["text"] = _("err_same_values")
                    return
                if temp not in groups:
                    info_label["text"] = _("err_group_not_exists")
                    return
                if temp2 in groups:
                    info_label["text"] = _("err_group_exists")
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.update_group(temp, temp2)
                    confirm_window.destroy()
                    info_label["text"] = _("success_edited")
                    groups[groups.index(temp)] = temp2
                    old_group.set(temp2)
                    old_group["values"] = groups

                self.confirmation_window(window, confirmation_window_yes)

            if _action == _("btn_delete"):
                temp2 = old_group.get()
                if not temp2:
                    info_label["text"] = _("err_empty_string").replace("строка", "выбор")
                    return
                if temp2 not in groups:
                    info_label["text"] = _("err_group_not_exists")
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.delete_group(temp2)
                    confirm_window.destroy()
                    info_label["text"] = _("success_deleted")
                    del groups[groups.index(temp2)]
                    old_group.set("")
                    old_group["values"] = groups

                self.confirmation_window(window, confirmation_window_yes)

        if action in (_("btn_add"), _("btn_edit")):
            group_label = tk.Label(frame, text=_("label_group"))
            group_label.grid(row=0, column=0, columnspan=2)
            group = ttk.Entry(frame, width=16)
            group.grid(row=1, column=0, columnspan=2)

        if action in (_("btn_edit"), _("btn_delete")):
            if action == _("btn_edit"):
                group_label["text"] = _("label_new_group")
                group_label.grid(row=0, column=1, columnspan=1, padx=10)
                group.grid(row=1, column=1, columnspan=1, padx=10)

            columnspan = 2 if action == _("btn_delete") else 1
            tk.Label(frame, text=_("label_old_group")).grid(row=0, column=0, columnspan=columnspan, padx=10)

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

    def student_window(self, action: str):
        window_geometry_x = f"{int(860 * sys_multiplier)}"
        window = tk.Toplevel(self.root)
        if action == _("btn_add"):
            window.title(_("title_add_student"))
        elif action == _("btn_edit"):
            window.title(_("title_edit_student"))
        elif action == _("btn_delete"):
            window.title(_("title_delete_student"))

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
                    old_surname["values"] = sorted(
                        {s[1] for s in students if s[0] == old_group.get() and s[1].lower().startswith(temp_surname)})
                else:
                    old_surname["values"] = []
            if combobox_name == "name":
                if temp_surname:
                    old_name["values"] = sorted({s[2] for s in students if
                                                 s[0] == old_group.get() and s[1] == old_surname.get() and s[
                                                     2].lower().startswith(temp_name)})
                else:
                    old_name["values"] = []
            if combobox_name == "patronymic":
                if temp_name:
                    old_patronymic["values"] = sorted(
                        {s[3] for s in students if
                         s[0] == old_group.get() and s[1] == old_surname.get() and s[2] == old_name.get() and s[
                             3].lower().startswith(temp_patronymic)})
                else:
                    old_patronymic["values"] = []

        def old_selected(event):
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
            if _action == _("btn_add"):
                temp_group = new_group.get()
                temp_surname = new_surname.get()
                temp_name = new_name.get()
                temp_patronymic = new_patronymic.get()
                if not temp_group:
                    info_label["text"] = _("err_no_group")
                    return
                if not temp_surname or not temp_name or not temp_patronymic:
                    info_label["text"] = _("err_empty_string").replace("Пустая строка",
                                                                       "Одна или несколько строк пусты")
                    return
                is_added = self.controller.db.insert_student(temp_group, temp_surname, temp_name, temp_patronymic)
                if not is_added:
                    info_label["text"] = _("err_student_exists")
                    return
                info_label["text"] = _("success_added")

            if _action == _("btn_edit"):
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
                    info_label["text"] = _("err_no_group").replace("выбрана", "выбрана \"старая\"")
                    return
                if not temp_new_group:
                    info_label["text"] = _("err_no_group").replace("выбрана", "выбрана \"новая\"")
                    return
                if not all(temp_old_student):
                    info_label["text"] = _("err_empty_string").replace("Пустая строка",
                                                                       "Один или несколько пустых выборов в \"Старом студенте\"")
                    return
                if not all(temp_new_student):
                    info_label["text"] = _("err_empty_string").replace("Пустая строка",
                                                                       "Один или несколько пустых строк в \"Новом студенте\"")
                    return
                if temp_old_student == temp_new_student:
                    info_label["text"] = _("err_same_values")
                    return
                if temp_old_student not in students:
                    info_label["text"] = _("err_student_not_exists")
                    return
                if temp_new_student in students:
                    info_label["text"] = _("err_student_exists")
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.update_student(*temp_old_student, *temp_new_student)
                    confirm_window.destroy()
                    info_label["text"] = _("success_edited")
                    students[students.index(temp_old_student)] = temp_new_student
                    old_surname.set(temp_new_surname)
                    old_name.set(temp_new_name)
                    old_patronymic.set(temp_new_patronymic)

                self.confirmation_window(window, confirmation_window_yes)

            if _action == _("btn_delete"):
                temp_group = old_group.get()
                temp_surname = old_surname.get()
                temp_name = old_name.get()
                temp_patronymic = old_patronymic.get()
                temp_student = (temp_group, temp_surname, temp_name, temp_patronymic)
                if not temp_group:
                    info_label["text"] = _("err_no_group")
                    return
                if not all(temp_student):
                    info_label["text"] = _("err_empty_string").replace("Пустая строка",
                                                                       "Один или несколько пустых выборов в \"Старом студенте\"")
                    return
                if temp_student not in students:
                    info_label["text"] = _("err_student_not_exists")
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.delete_student(*temp_student)
                    confirm_window.destroy()
                    info_label["text"] = _("success_deleted")
                    del students[students.index(temp_student)]
                    old_group.set("")
                    old_surname.set("")
                    old_name.set("")
                    old_patronymic.set("")

                self.confirmation_window(window, confirmation_window_yes)

        if action in (_("btn_add"), _("btn_edit")):
            new_student = tk.Frame(frame)
            new_student_label = tk.Label(new_student, text=_("label_new_student") + ":")
            new_student_label.grid(row=0, column=0, columnspan=4)

            new_group_label = tk.Label(new_student, text=_("label_group"))
            new_surname_label = tk.Label(new_student, text=_("label_surname"))
            new_name_label = tk.Label(new_student, text=_("label_name"))
            new_patronymic_label = tk.Label(new_student, text=_("label_patronymic"))

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

        if action in (_("btn_edit"), _("btn_delete")):
            if action == _("btn_edit"):
                window.geometry(f"{window_geometry_x}x260")
                new_student.grid(row=1, column=0, pady=10)

            old_student = tk.Frame(frame)
            old_student_label = tk.Label(old_student, text=_("label_old_student") + ":")
            old_student_label.grid(row=0, column=0, columnspan=4)

            old_group_label = tk.Label(old_student, text=_("label_group"))
            old_surname_label = tk.Label(old_student, text=_("label_surname"))
            old_name_label = tk.Label(old_student, text=_("label_name"))
            old_patronymic_label = tk.Label(old_student, text=_("label_patronymic"))

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
            if action == _("btn_edit"):
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

    def lesson_window(self, action: str):
        window_geometry_x = f"{int(500 * sys_multiplier)}"
        window = tk.Toplevel(self.root)
        if action == _("btn_add"):
            window.title(_("title_add_lesson"))
        elif action == _("btn_edit"):
            window.title(_("title_edit_lesson"))
        elif action == _("btn_delete"):
            window.title(_("title_delete_lesson"))

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
            if _action == _("btn_add"):
                temp = lesson.get()
                if not temp:
                    info_label["text"] = _("err_empty_string")
                    return
                is_added = self.controller.db.insert_lesson(temp)
                if not is_added:
                    info_label["text"] = _("err_lesson_exists")
                    return
                info_label["text"] = _("success_added")

            if _action == _("btn_edit"):
                temp = old_lesson.get()
                temp2 = lesson.get()
                if not temp or not temp2:
                    info_label["text"] = _("err_empty_string") + "\n" + _("err_no_lesson").replace("выбран",
                                                                                                   "выбор или строка")
                    return
                if temp2 == temp:
                    info_label["text"] = _("err_same_values")
                    return
                if temp not in lessons:
                    info_label["text"] = _("err_lesson_not_exists")
                    return
                if temp2 in lessons:
                    info_label["text"] = _("err_lesson_exists")
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.update_lesson(temp, temp2)
                    confirm_window.destroy()
                    info_label["text"] = _("success_edited")
                    lessons[lessons.index(temp)] = temp2
                    old_lesson.set(temp2)
                    old_lesson["values"] = lessons

                self.confirmation_window(window, confirmation_window_yes)

            if _action == _("btn_delete"):
                temp2 = old_lesson.get()
                if not temp2:
                    info_label["text"] = _("err_empty_string").replace("строка", "выбор")
                    return
                if temp2 not in lessons:
                    info_label["text"] = _("err_lesson_not_exists")
                    return

                def confirmation_window_yes(confirm_window):
                    self.controller.db.delete_lesson(temp2)
                    confirm_window.destroy()
                    info_label["text"] = _("success_deleted")
                    del lessons[lessons.index(temp2)]
                    old_lesson.set("")
                    old_lesson["values"] = lessons

                self.confirmation_window(window, confirmation_window_yes)

        if action in (_("btn_add"), _("btn_edit")):
            lesson_label = tk.Label(frame, text=_("label_lesson"))
            lesson_label.grid(row=0, column=0, columnspan=2)
            lesson = ttk.Entry(frame, width=30)
            lesson.grid(row=1, column=0, columnspan=2)

        if action in (_("btn_edit"), _("btn_delete")):
            if action == _("btn_edit"):
                lesson_label["text"] = _("label_new_lesson")
                lesson_label.grid(row=0, column=1, columnspan=1, padx=10)
                lesson.grid(row=1, column=1, columnspan=1, padx=10)

            columnspan = 2 if action == _("btn_delete") else 1
            tk.Label(frame, text=_("label_old_lesson")).grid(row=0, column=0, columnspan=columnspan, padx=10)

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

    def about_window(self):
        about = tk.Toplevel(self.root)
        about.title(_("title_about"))
        about.geometry("600x550")
        about.resizable(False, False)

        content_frame = tk.Frame(about, padx=10, pady=10)
        content_frame.pack(expand=True, fill="both")

        try:
            photo = tk.PhotoImage(file="resources/images/program.png")
            img_label = tk.Label(content_frame, image=photo)
            img_label.image = photo
            img_label.pack(pady=(5, 10))
        except Exception as e:
            tk.Label(content_frame, text=f"Ошибка загрузки изображения: {e}", fg="red").pack()

        tk.Label(content_frame, text=_("text_about_program"),
                 font=("Arial", 12, "bold")).pack()
        tk.Label(content_frame, text=_("text_program_capabilities"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_capability_1"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_capability_2"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_capability_3"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_capability_4"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_version"), font=("Arial", 12)).pack()

        tk.Button(content_frame, text=_("btn_close"), command=about.destroy,
                  font=("Arial", 10)).pack(pady=10)

    def about_author(self):
        about = tk.Toplevel(self.root)
        about.title(_("title_about_author"))
        about.geometry("800x740")
        about.resizable(False, False)

        content_frame = tk.Frame(about, padx=10, pady=10)
        content_frame.pack(expand=True, fill="both")

        try:
            photo = tk.PhotoImage(file="resources/images/aboutPreview.png")
            img_label = tk.Label(content_frame, image=photo)
            img_label.image = photo
            img_label.pack(pady=(5, 10))
        except Exception as e:
            tk.Label(content_frame, text=f"Ошибка загрузки изображения: {e}", fg="red").pack()

        tk.Label(content_frame, text=_("text_author"), font=("Arial", 14, "bold")).pack()
        tk.Label(content_frame, text=_("text_author_group"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_author_name"), font=("Arial", 12)).pack()
        tk.Label(content_frame, text=_("text_author_email"), font=("Arial", 12), fg="blue").pack(pady=(0, 10))

        tk.Button(content_frame, text=_("btn_back"), command=about.destroy,
                  font=("Arial", 10)).pack(pady=10)

    def test_data_window(self):
        def yes_command():
            self.controller.db.test_data()
            test_data.destroy()

        test_data = tk.Toplevel(self.root)
        test_data.title(_("title_test_data"))
        test_data.geometry("250x100")
        test_data.resizable(False, False)

        tk.Label(test_data, text=_("confirm_test_data")).pack()
        tk.Label(test_data, text=_("label_test_data_count")).pack()
        test_data_grid = tk.Frame(test_data)
        tk.Button(test_data_grid, text=_("btn_no"), command=test_data.destroy).grid(row=0, column=0)
        tk.Button(test_data_grid, text=_("btn_yes"), command=yes_command).grid(row=0, column=1)
        test_data_grid.pack()

    def db_clear_window(self):
        def yes_command():
            self.controller.db.clear()
            clear.destroy()

        clear = tk.Toplevel(self.root)
        clear.title(_("title_clear_db"))
        clear.geometry("200x80")
        clear.resizable(False, False)

        tk.Label(clear, text=_("confirm_clear_db")).pack()
        clear_grid = tk.Frame(clear)
        tk.Button(clear_grid, text=_("btn_no"), command=clear.destroy).grid(row=0, column=0)
        tk.Button(clear_grid, text=_("btn_yes"), command=yes_command).grid(row=0, column=1)
        clear_grid.pack()

    def close_program(self):
        """Закрыть программу"""
        if hasattr(self.controller, 'save_current_state'):
            self.controller.save_current_state()

        # Закрываем БД и окно
        self.controller.db.close()
        self.root.destroy()

        # Принудительно завершаем процесс
        import os
        os._exit(0)

    def auto_save_state(self):
        if hasattr(self.controller, 'save_current_state'):
            self.root.after(1000, self.controller.save_current_state)

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
                showerror(title=_("err_no_data"),
                          message=_("err_no_data") + "\n" + _("err_no_data") + ".")
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
                    self.controller.db._db.execute(
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

            self.controller.db._db.commit()
            showinfo(title=_("success_saved"), message=_("success_saved") + ".")

        def force_create_spreadsheet(self):
            """Принудительно создать таблицу с текущими значениями"""
            if all([self.year.get(), self.month.get(), self.groups.get(), self.lessons.get()]):
                # Вызываем filtering для создания таблицы
                self.filtering()

        def filtering():
            if self.year.get():
                self.month["values"] = [""] + self._get_date("month", self.year.get())
            else:
                self.month.set("")
                self.month["values"] = []

            # Сохраняем состояние при каждом изменении
            if hasattr(self.controller, 'save_current_state'):
                # Обновляем состояние в контроллере
                self.controller.current_state["selected_year"] = self.year.get()
                self.controller.current_state["selected_month"] = self.month.get()
                self.controller.current_state["selected_group"] = self.groups.get()
                self.controller.current_state["selected_lesson"] = self.lessons.get()
                # Асинхронное сохранение
                self.root.after(500, self.controller.save_current_state)

            if all([self.year.get(), self.month.get(), self.groups.get(), self.lessons.get()]):
                self._update_spreadsheet_only()
                create_spreadsheet()
            else:
                self._update_spreadsheet_only()

        filtering_frame = tk.Frame(self.root)

        for c in range(4):
            filtering_frame.columnconfigure(index=c, weight=1)

        tk.Label(filtering_frame, text=_("label_year") + ":").grid(row=0, column=0)
        tk.Label(filtering_frame, text=_("label_month") + ":").grid(row=0, column=1)
        tk.Label(filtering_frame, text=_("label_group") + ":").grid(row=0, column=2)
        tk.Label(filtering_frame, text=_("label_lesson") + ":").grid(row=0, column=3)

        self.year = ttk.Combobox(filtering_frame, width=10, state="readonly")
        self.month = ttk.Combobox(filtering_frame, width=10, state="readonly")
        self.groups = ttk.Combobox(filtering_frame, width=10, state="readonly")
        self.lessons = ttk.Combobox(filtering_frame, width=30, state="readonly")

        self.year.bind("<<ComboboxSelected>>", lambda event: (filtering(), self.auto_save_state()))
        self.month.bind("<<ComboboxSelected>>", lambda event: (filtering(), self.auto_save_state()))
        self.groups.bind("<<ComboboxSelected>>", lambda event: (filtering(), self.auto_save_state()))
        self.lessons.bind("<<ComboboxSelected>>", lambda event: (filtering(), self.auto_save_state()))

        self.year.grid(row=1, column=0)
        self.month.grid(row=1, column=1)
        self.groups.grid(row=1, column=2)
        self.lessons.grid(row=1, column=3)

        filtering_frame.pack(fill="x", pady=5)

        self.spreadsheet = CustomSpreadsheet(self.root)
        self.spreadsheet.pack(fill="both", expand=True)

        bottom = tk.Frame(self.root)
        bottom.pack(side="bottom", fill="x")

        bottom_color_labels = tk.Frame(bottom)
        bottom_color_labels.pack()

        bottom_buttons = tk.Frame(bottom)
        bottom_buttons.pack(side="bottom")

        tk.Button(bottom_buttons, text=_("btn_save"), command=save_spreadsheet).pack(side="left")
        tk.Button(bottom_buttons, text=_("btn_reset"), command=self.main_frame_reset).pack(side="right")

        color_placeholder = " " * 4
        tk.Label(bottom_color_labels, text=color_placeholder, bg="green").pack(side="left")
        tk.Label(bottom_color_labels, text=_("warning_missed_hours_0") + _("warning_separator")).pack(side="left")
        tk.Label(bottom_color_labels, text=color_placeholder, bg="yellow").pack(side="left")
        tk.Label(bottom_color_labels, text=_("warning_missed_hours_1") + _("warning_separator")).pack(side="left")
        tk.Label(bottom_color_labels, text=color_placeholder, bg="red").pack(side="left")
        tk.Label(bottom_color_labels, text=_("warning_missed_hours_2")).pack(side="left")

        #self.main_frame_reset()
        self._initial_main_frame_setup()

    def _update_spreadsheet_only(self):
        """Обновить только таблицу без сброса значений комбобоксов"""
        self.spreadsheet.clear()

    def _load_combobox_values(self):
        """Загрузить доступные значения в комбобоксы"""
        # Годы
        self.year["values"] = [""] + [i for i in self._get_date()]

        # Месяцы (зависит от выбранного года)
        selected_year = self.year.get()
        if selected_year:
            self.month["values"] = [""] + [i for i in self._get_date("month", selected_year)]
        else:
            self.month["values"] = []

        # Группы
        groups_data = self.controller.db.having_individual_return("Groups", ["group"], ["group"])
        self.groups["values"] = [""] + [i[0] for i in groups_data] if groups_data else [""]

        # Предметы
        lessons_data = self.controller.db.having_individual_return("Lessons", ["lesson"], ["lesson"])
        self.lessons["values"] = [""] + [i[0] for i in lessons_data] if lessons_data else [""]

    def _initial_main_frame_setup(self):
        """Начальная настройка основного фрейма без перезаписи сохраненного состояния"""
        # Очищаем таблицу
        self.spreadsheet.clear()

        # Загружаем доступные значения в комбобоксы
        self.year["values"] = [""] + [i for i in self._get_date()]
        self.month["values"] = []  # Будет установлено при выборе года
        groups_data = self.controller.db.having_individual_return("Groups", ["group"], ["group"])
        self.groups["values"] = [""] + [i[0] for i in groups_data] if groups_data else [""]
        lessons_data = self.controller.db.having_individual_return("Lessons", ["lesson"], ["lesson"])
        self.lessons["values"] = [""] + [i[0] for i in lessons_data] if lessons_data else [""]

    def main_frame_reset(self, only_spreadsheet: bool = False, only_combobox_values: bool = False):
        def clear_combobox_values():
            self.year["values"] = [""] + [i for i in self._get_date()]
            if self.year.get():
                self.month["values"] = [""] + [i for i in self._get_date("month", self.year.get())]
            else:
                self.month["values"] = []
            self.groups["values"] = [""] + [i[0] for i in
                                            self.controller.db.having_individual_return("Groups", ["group"], ["group"])]
            self.lessons["values"] = [""] + [i[0] for i in
                                             self.controller.db.having_individual_return("Lessons", ["lesson"],
                                                                                         ["lesson"])]

        if only_combobox_values:
            clear_combobox_values()
            return

        # Если only_spreadsheet=True, очищаем только таблицу
        self.spreadsheet.clear()

        if only_spreadsheet:
            return

        # Только если явно вызвано без флагов - сбрасываем значения
        # Это происходит когда пользователь нажимает кнопку "Сброс"
        today = datetime.now()
        self.year.set(str(today.year))
        self.month.set(f"0{today.month}" if today.month < 10 else str(today.month))
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
        cursor = self.controller.db._db.cursor()
        cursor.execute(command)
        result = cursor.fetchall()
        cursor.close()
        if select_type == "month":
            return [i[1] for i in result]
        if select_type == "day":
            return [i[2] for i in result]
        return [i[0] for i in result]