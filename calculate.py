import tkinter as tk
from tkinter import messagebox
import math


class ProCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор Pro")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        self.colors = {
            "bg_main": "#FFFFFF",
            "text_main": "#212121",
            "text_sec": "#8E8E93",
            "btn_num_bg": "#F2F2F7",
            "btn_num_fg": "#000000",
            "btn_num_hov": "#E5E5EA",
            "btn_op_bg": "#6E6574",
            "btn_op_fg": "#FFFFFF",
            "btn_op_hov": "#5E5663",
            "btn_fn_bg": "#D1D1D6",
            "btn_fn_fg": "#000000",
            "btn_fn_hov": "#AEAEB2",
            "btn_eq_bg": "#443D44",
            "btn_eq_fg": "#FFFFFF",
            "btn_eq_hov": "#363036",
            "btn_del_bg": "#D1D1D6",
            "btn_del_fg": "#000000",
            "btn_del_hov": "#AEAEB2",
        }

        self.root.configure(bg=self.colors["bg_main"])

        self.var_main = tk.StringVar()
        self.var_expression = tk.StringVar()
        self.history_data = []

        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_main"])
        self.main_frame.pack(fill="both", expand=True)

        self._build_display()
        self._build_keyboard()
        self._bind_hotkeys()

    def _build_display(self):
        """Дисплей."""
        display_frame = tk.Frame(self.main_frame, bg=self.colors["bg_main"])
        display_frame.pack(expand=True, fill="x", padx=20, pady=(20, 10))

        self.lbl_expr = tk.Label(
            display_frame,
            textvariable=self.var_expression,
            font=("Segoe UI", 16),
            bg=self.colors["bg_main"],
            fg=self.colors["text_sec"],
            anchor="e",
        )
        self.lbl_expr.pack(side="top", fill="x", pady=(10, 0))

        self.entry = tk.Entry(
            display_frame,
            textvariable=self.var_main,
            font=("Segoe UI", 43, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["text_main"],
            bd=1,
            justify="right",
            highlightthickness=0,
        )
        self.entry.pack(side="bottom", fill="x")

        vcmd = (self.root.register(self._validate_input), "%S")
        self.entry.configure(validate="key", validatecommand=vcmd)

    def _validate_input(self, char):
        """Разрешает только цифры, точку и основные операторы."""
        allowed_chars = "0123456789.+-*/"

        if char == "":
            return True

        return char in allowed_chars

    def _build_keyboard(self):
        """Клавиатура."""
        btns_frame = tk.Frame(self.main_frame, bg=self.colors["bg_main"])
        btns_frame.pack(expand=True, fill="both", padx=15, pady=15)

        for i in range(5):
            btns_frame.rowconfigure(i, weight=1)
        for i in range(4):
            btns_frame.columnconfigure(i, weight=1)

        layout = [
            ("C", 0, 0, "fn"),
            ("H", 0, 1, "fn"),
            ("⌫", 0, 2, "del"),
            ("/", 0, 3, "op"),
            ("7", 1, 0, "num"),
            ("8", 1, 1, "num"),
            ("9", 1, 2, "num"),
            ("*", 1, 3, "op"),
            ("4", 2, 0, "num"),
            ("5", 2, 1, "num"),
            ("6", 2, 2, "num"),
            ("-", 2, 3, "op"),
            ("1", 3, 0, "num"),
            ("2", 3, 1, "num"),
            ("3", 3, 2, "num"),
            ("+", 3, 3, "op"),
            ("0", 4, 0, "num"),
            (".", 4, 1, "num"),
            ("√", 4, 2, "fn"),
            ("=", 4, 3, "eq"),
        ]

        for item in layout:
            text, r, c, btype = item

            if btype == "num":
                bg, fg, hov = (
                    self.colors["btn_num_bg"],
                    self.colors["btn_num_fg"],
                    self.colors["btn_num_hov"],
                )
                cmd = lambda t=text: self._add_char(t)
            elif btype == "op":
                bg, fg, hov = (
                    self.colors["btn_op_bg"],
                    self.colors["btn_op_fg"],
                    self.colors["btn_op_hov"],
                )
                cmd = lambda t=text: self._add_char(t)
            elif btype == "fn":
                bg, fg, hov = (
                    self.colors["btn_fn_bg"],
                    self.colors["btn_fn_fg"],
                    self.colors["btn_fn_hov"],
                )
                if text == "C":
                    cmd = self._clear
                elif text == "√":
                    cmd = self._calc_sqrt
                elif text == "H":
                    cmd = self._show_history_window
            elif btype == "del":
                bg, fg, hov = (
                    self.colors["btn_del_bg"],
                    self.colors["btn_del_fg"],
                    self.colors["btn_del_hov"],
                )
                cmd = self._backspace
            elif btype == "eq":
                bg, fg, hov = (
                    self.colors["btn_eq_bg"],
                    self.colors["btn_eq_fg"],
                    self.colors["btn_eq_hov"],
                )
                cmd = self._calculate

            btn = tk.Button(
                btns_frame,
                text=text,
                font=("Segoe UI", 16),
                bg=bg,
                fg=fg,
                relief="flat",
                activebackground=hov,
                activeforeground=fg,
                cursor="hand2",
                bd=0,
                command=cmd,
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)

            btn.bind("<Enter>", lambda e, b=btn, c=hov: b.configure(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=bg: b.configure(bg=c))

    def _bind_hotkeys(self):
        """Горячие клавиши."""
        self.root.bind("<Return>", lambda e: self._calculate())
        self.root.bind("<KP_Enter>", lambda e: self._calculate())
        self.root.bind("<Escape>", lambda e: self._clear())
        self.root.bind("<BackSpace>", self._backspace_event)

    def _add_char(self, char):
        """Вставляет символ в текущее положение курсора и прокручивает экран."""
        idx = self.entry.index(tk.INSERT)
        self.entry.insert(idx, char)
        self.entry.xview_moveto(1)

    def _backspace(self):
        """
        Удаляет символ.
        Используется только кнопкой '⌫' на калькуляторе.
        """
        if self.entry.selection_present():
            self.entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            cursor_pos = self.entry.index(tk.INSERT)
            if cursor_pos > 0:
                self.entry.delete(cursor_pos - 1, cursor_pos)

        self.entry.xview_moveto(1)

    def _backspace_event(self, event):
        """Обработка Backspace с клавиатуры."""
        if self.root.focus_get() == self.entry:
            return

        self._backspace()
        return "break"

    def _clear(self):
        """Очищает обе строки дисплея."""
        self.var_main.set("")
        self.var_expression.set("")

    def _format_result(self, res):
        """Форматирует результат, используя научную нотацию, если число слишком длинное."""
        DISPLAY_LIMIT = 15

        if isinstance(res, float):
            if math.isinf(res):
                return "inf" if res > 0 else "-inf"
            if math.isnan(res):
                return "NaN"

            if res.is_integer():
                res_str = str(int(res))
            else:
                res_str_rounded = f"{round(res, 8)}"
                if len(res_str_rounded) <= DISPLAY_LIMIT:
                    return res_str_rounded

                return "{:.8e}".format(res)

        res_str = str(res)
        if len(res_str) > DISPLAY_LIMIT:
            return "{:.8e}".format(float(res))

        return res_str

    def _show_history_window(self):
        """Открывает красивое и растягиваемое окно истории."""
        hist_win = tk.Toplevel(self.root)
        hist_win.title("История")
        hist_win.geometry("450x550")
        hist_win.configure(bg="#F9F9F9")

        hist_win.columnconfigure(0, weight=1)
        hist_win.rowconfigure(0, weight=1)

        frame_text = tk.Frame(hist_win, bg="#F9F9F9")
        frame_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_area = tk.Text(
            frame_text,
            font=("Consolas", 13),
            bg="#FFFFFF",
            bd=0,
            padx=15,
            pady=15,
            yscrollcommand=scrollbar.set,
        )
        text_area.pack(side=tk.LEFT, expand=True, fill="both")
        scrollbar.config(command=text_area.yview)

        text_area.tag_config("expr", foreground="#888888")
        text_area.tag_config("res", foreground="#000000", font=("Consolas", 14, "bold"))
        text_area.tag_config("sep", foreground="#DDDDDD")

        if not self.history_data:
            text_area.insert("1.0", "История пуста")
        else:
            for expr, res in reversed(self.history_data):
                text_area.insert(tk.END, f"{expr}\n", "expr")
                text_area.insert(tk.END, f"= {res}\n", "res")
                text_area.insert(tk.END, "-" * 40 + "\n", "sep")

        text_area.configure(state="disabled")

        btn_clear = tk.Button(
            hist_win,
            text="Очистить всё",
            relief="flat",
            bg="#FF3B30",
            fg="white",
            command=lambda: [self.history_data.clear(), hist_win.destroy()],
        )
        btn_clear.grid(row=1, column=0, pady=10, ipadx=10)

    def _add_log(self, expr, res):
        """Сохраняет выражение и результат в историю."""
        self.history_data.append((expr, res))

    def _calc_sqrt(self):
        """Вычисляет квадратный корень."""
        try:
            val_str = self.var_main.get()
            if not val_str:
                return
            val = float(val_str)
            if val < 0:
                messagebox.showerror("Ошибка", "Корень из отрицательного числа!")
                self.var_main.set("")
            else:
                res = math.sqrt(val)
                res_str = self._format_result(res)

                self.var_expression.set(f"√({val_str}) =")
                self.var_main.set(res_str)
                self._add_log(f"√({val_str})", res_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный ввод!")
        except Exception:
            messagebox.showerror("Ошибка", "Ошибка вычисления")

    def _calculate(self):
        """Основные вычисления."""
        expr = self.var_main.get()
        if not expr:
            return
        try:
            res = eval(expr)

            res_str = self._format_result(res)

            self.var_expression.set(expr + " =")
            self.var_main.set(res_str)
            self.entry.icursor(tk.END)
            self._add_log(expr, res_str)

            self.entry.xview_moveto(1)

        except ZeroDivisionError:
            messagebox.showerror("Ошибка", "Деление на ноль!")
        except SyntaxError:
            messagebox.showerror("Ошибка", "Ошибка в выражении!")
        except Exception:
            messagebox.showerror("Ошибка", "Ошибка вычисления")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProCalculator(root)
    root.mainloop()
