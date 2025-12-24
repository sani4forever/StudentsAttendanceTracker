from typing import List, Dict, Iterable
import tkinter as tk

class AutoHidingScrollbar(tk.Scrollbar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PACK_INFO = ""

    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
            self.tk.call("pack", "forget", self)
        else:
            self.pack()
        tk.Scrollbar.set(self, low, high)

    def pack(self, **kw):
        if not self.PACK_INFO:
            self.PACK_INFO = kw
        super().pack(**self.PACK_INFO)

    def grid(self, **kw):
        raise (tk.TclError, "grid cannot be used with this widget")

    def place(self, **kw):
        raise (tk.TclError, "place cannot be used  with this widget")


class CustomLabel(tk.Label):
    def __init__(self,
                 master: tk.Misc = None,
                 set_value: str = None,
                 menu_values: List = None,
                 custom_info: dict = None,
                 **kwargs):
        super().__init__(master, **kwargs)
        self._info = custom_info if custom_info else {}
        self._colors = {}
        self._default_bg = None
        var = tk.StringVar()
        var.set(set_value)
        self["textvariable"] = var
        # self.bind("<Button-1>", lambda e: print(self._info))  # TODO: remove
        self.bind("<Button-1>", lambda e: self.create_menu(e, var, menu_values))

    def create_menu(self, main_event: tk.Event, main_variable: tk.Variable, variables_list: List):
        def _variable_set(value):
            main_variable.set(value)
            if str(value) in self._colors:
                self.config(bg=self._colors[str(value)])
            else:
                self.config(bg=self._default_bg if self._default_bg else self.cget("bg"))
            main_menu.destroy()

        def _destroy_menu(event):  # noqa
            pass
            # if event.widget is main_menu:
            #     print(event.widget)  # TODO: some stuff needed here, if one of the variables is bigger than the others
            # event.widget.destroy()

        main_menu = tk.Toplevel()
        # TODO: choose between <Button-1> and <Leave>
        # main_menu.bind("<Button-1>", lambda e: e.widget.destroy())  # For destroying menu on clicking outside
        main_menu.bind("<Leave>", lambda e: _destroy_menu(e))  # For destroying menu when leaving it
        main_menu.overrideredirect(True)  # Removes border

        default_bg = main_menu.cget("bg")  # Store default background color

        for txt in variables_list:
            my_lab = tk.Label(main_menu, text=txt, padx=10, pady=6,
                              borderwidth=2, relief="solid",
                              font=("Noto Sans Mono", 15))  # TkFixedFont if needed
            my_lab.pack(side='top')
            my_lab.bind('<Enter>', lambda _e: _e.widget.config(bg='gray'))
            my_lab.bind('<Leave>', lambda _e: _e.widget.config(bg=default_bg))
            my_lab.bind('<Button-1>', lambda _e: _variable_set(_e.widget.cget("text")))

        main_menu.update_idletasks()
        main_menu.grab_set()
        w = main_menu.winfo_width()
        h = main_menu.winfo_height()
        main_menu.geometry("%dx%d+%d+%d" % (w, h, main_event.x_root, main_event.y_root + 10))

    @property
    def colors(self):
        return self._colors

    @colors.setter
    def colors(self, colors: Dict[str, str]):
        self._colors = colors

    @property
    def default_bg(self):
        return self._default_bg

    @default_bg.setter
    def default_bg(self, value: str):
        self._default_bg = value

    @property
    def custom_info(self) -> dict:
        return self._info if self._info else {"info": None}

    @custom_info.setter
    def custom_info(self, value: dict) -> None:
        self._info = value


class CustomSpreadsheet(tk.Frame):
    def __init__(self,
                 master: tk.Misc = None,
                 columns: int = 0,
                 rows: int = 0,
                 columns_headers: Iterable = None,
                 rows_headers: Iterable = None,
                 set_values: Iterable[Iterable] = None,
                 cells_values: Iterable[Iterable[Iterable]] = None,
                 cells_colors: Dict[str, str] = None,
                 **kwargs):
        super().__init__(master, **kwargs)
        self._cells = {}

        self._canvas = None

        self._frame = None
        self._ver_scrollbar = None
        self._hor_scrollbar = None

        self.create(columns=columns,
                    rows=rows,
                    columns_headers=columns_headers,
                    rows_headers=rows_headers,
                    set_values=set_values,
                    cells_values=cells_values,
                    cells_colors=cells_colors,
                    ignore_errors=True)

    def create(self,
               columns: int = 0,
               rows: int = 0,
               columns_headers: Iterable = None,
               rows_headers: Iterable = None,
               set_values: Iterable[Iterable] = None,
               cells_values: Iterable[Iterable[Iterable]] = None,
               cells_colors: Dict[str, str] = None,
               ignore_errors: bool = False) -> bool:
        def custom_cell_color(value):
            if str(value) in cells_colors:
                return cells_colors[str(value)]
            return None

        errors = []
        critical_error = False
        if columns == 0 or rows == 0:
            errors.append("WARNING: columns or rows for CustomSpreadsheet are 0")
            critical_error = True
        if columns_headers is None:
            errors.append("WARNING: columns headers for CustomSpreadsheet are 0")
            columns_headers = tuple("" for _ in range(columns))
        if rows_headers is None:
            errors.append("WARNING: rows headers for CustomSpreadsheet are 0")
            rows_headers = tuple("" for _ in range(rows))
        if set_values is None:
            errors.append("WARNING: set values for CustomSpreadsheet are None")
            set_values = tuple()
        if cells_values is None:
            errors.append("WARNING: values for CustomSpreadsheet are None")
            cells_values = tuple()
        if cells_colors is None:
            cells_colors = {}

        if not ignore_errors:
            for i in errors:
                print(i)

        if critical_error:
            return False

        self._canvas = tk.Canvas(self)

        self._frame = tk.Frame(self._canvas)

        self._ver_scrollbar = AutoHidingScrollbar(self._canvas, command=self._canvas.yview, orient="vertical")
        self._hor_scrollbar = AutoHidingScrollbar(self._canvas, command=self._canvas.xview, orient="horizontal")

        self._canvas.configure(xscrollcommand=self._hor_scrollbar.set,
                               yscrollcommand=self._ver_scrollbar.set)

        self._canvas.create_window((0, 0), window=self._frame, anchor="nw")

        self._ver_scrollbar.pack(side="right", fill="y")
        self._hor_scrollbar.pack(side="bottom", fill="x")
        self._canvas.pack(side="top", fill="both", expand=True)

        for r in range(rows):
            tk.Label(self._frame, text=rows_headers[r]).grid(row=r + 1, column=0, sticky="w")
            self._cells[f"{r}__{rows_headers[r]}"] = {}
            for c in range(columns):
                if r == 0:
                    tk.Label(self._frame, text=columns_headers[c]).grid(row=0, column=c + 1)
                if str(set_values[r][c]) in cells_colors:
                    bg = cells_colors[str(set_values[r][c])]
                else:
                    bg = None
                entry = CustomLabel(self._frame,
                                    width=3,
                                    justify="center",
                                    borderwidth=1,
                                    relief="solid",
                                    font=("Arial", 15),
                                    set_value=set_values[r][c],
                                    menu_values=cells_values[r][c])
                default_bg = entry.cget("bg")
                entry.colors = cells_colors
                entry.default_bg = default_bg
                entry.config(bg=bg if bg else default_bg)
                entry.bind('<Enter>', lambda _e: _e.widget.config(bg='gray'))
                entry.bind('<Leave>', lambda _e:
                _e.widget.config(
                    bg=custom_cell_color(_e.widget.cget("text"))
                    if str(_e.widget.cget("text")) in cells_colors
                    else default_bg
                ))
                entry.grid(row=r + 1, column=c + 1)
                self._cells[f"{r}__{rows_headers[r]}"][f"{c}__{columns_headers[c]}"] = entry

        tk.Label(self._frame, text="", padx=8).grid(row=9998, column=9998)

        self._canvas.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

        return True

    def clear(self):
        if self._canvas:
            self._canvas.destroy()
        if self._cells:
            self._cells.clear()

    @property
    def cells(self) -> Dict[str, Dict[str, CustomLabel]]:
        return self._cells


class Main:
    def __init__(self):
        def create_spreadsheet():
            spreadsheet.create(
                columns=spreadsheet_width,
                rows=spreadsheet_height,
                columns_headers=days,
                rows_headers=students,
                set_values=spreadsheet_set_values,
                cells_values=spreadsheet_cells_values,
                cells_colors=colors
            )

        def spreadsheet_recreate():
            spreadsheet.clear()
            create_spreadsheet()

        def print_cells():
            # print(spreadsheet.cells)
            for row_header, row in spreadsheet.cells.items():
                for column_header, cell in row.items():
                    print(f"{cell.cget('text')}", end=" ;; ")
                print()

        self.root = tk.Tk()
        self.root.title("Главное окно")
        self.root.geometry("500x500")
        # self.root.resizable(False, False)  # TODO: remove
        self.root.bind("<Escape>", lambda _: exit())
        self.root.bind("<Control-q>", lambda _: exit())
        self.root.bind("<Control-Q>", lambda _: exit())
        self.root.bind("<Control-w>", lambda _: self.root.iconify())
        self.root.bind("<Control-W>", lambda _: self.root.iconify())

        days = tuple(i for i in range(1, 32))
        students = tuple(f"Ученик {i}" for i in range(1, 21))

        spreadsheet_width = len(days)
        spreadsheet_height = len(students)

        spreadsheet_set_values = tuple(
            tuple(
                # randint(10, 99)
                0
                for _ in range(spreadsheet_width))
            for _ in range(spreadsheet_height)
        )

        spreadsheet_cells_values = tuple(
            tuple(
                (0, 1, 2, "ababa")
                # tuple([randint(10, 99) for _ in range(4)])
                for _ in range(spreadsheet_width)
            )
            for _ in range(spreadsheet_height)
        )

        colors = {
            "0": "green",
            "1": "yellow",
            "2": "red",
        }

        tk.Button(self.root, text="recreate", command=spreadsheet_recreate).pack()
        tk.Button(self.root, text="print cells", command=print_cells).pack()
        spreadsheet = CustomSpreadsheet(self.root)
        spreadsheet.pack(fill="both", expand=True)
        create_spreadsheet()

        self.root.mainloop()


if __name__ == "__main__":
    Main()
