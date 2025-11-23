import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from faker import Faker

COLORS = {
    "primary": "#007AFF",
    "primary_hover": "#0056b3",
    "bg": "#FFFFFF",
    "bg_alt": "#F5F5F7",
    "text": "#333333",
    "header_text": "#FFFFFF",
    "danger": "#FF3B30",
}

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FILE_DB = "patients_db.json"
FAKE = Faker("ru_RU")


class PatientManager:
    """Класс для управления данными (Logic Layer)"""

    def __init__(self):
        self.patients = self.load_data()

    def load_data(self):
        if not os.path.exists(FILE_DB):
            data = self.generate_initial_data(10)
            self.patients = data
            self.save_data()
            return data
        try:
            with open(FILE_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_data(self):
        with open(FILE_DB, "w", encoding="utf-8") as f:
            json.dump(self.patients, f, indent=4, ensure_ascii=False)

    def calculate_bmi(self, weight, height):
        """ИМТ = вес (кг) / рост (м)^2"""
        try:
            h_m = height / 100
            return round(weight / (h_m**2), 2)
        except ZeroDivisionError:
            return 0

    def generate_initial_data(self, count=10):
        data = []
        for _ in range(count):
            gender = FAKE.random_element(["М", "Ж"])

            if gender == "М":
                name = FAKE.name_male()
            else:
                name = FAKE.name_female()

            age = FAKE.random_int(min=18, max=80)
            height = FAKE.random_int(min=150, max=195)
            weight = FAKE.random_int(min=50, max=120)

            patient = {
                "name": name,
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
            }
            patient["bmi"] = self.calculate_bmi(patient["weight"], patient["height"])
            data.append(patient)
        return data

    def add_patient(self, data):
        data["bmi"] = self.calculate_bmi(data["weight"], data["height"])
        self.patients.append(data)
        self.save_data()

    def update_patient(self, index, data):
        data["bmi"] = self.calculate_bmi(data["weight"], data["height"])
        self.patients[index] = data
        self.save_data()

    def delete_patient(self, index: int):
        """Удаляет пациента по индексу из списка и сохраняет данные."""
        if 0 <= index < len(self.patients):
            del self.patients[index]
            self.save_data()
            return True
        return False

    def get_stats(self):
        """Подготовка данных для графиков"""
        if not self.patients:
            return None

        genders = [p["gender"] for p in self.patients]
        ages = [p["age"] for p in self.patients]
        bmis = [p["bmi"] for p in self.patients]

        bmi_male = [p["bmi"] for p in self.patients if p["gender"] == "М"]
        bmi_female = [p["bmi"] for p in self.patients if p["gender"] == "Ж"]

        return {
            "genders": genders,
            "ages": ages,
            "bmis": bmis,
            "bmi_by_sex": (bmi_male, bmi_female),
        }


class PatientForm(tk.Toplevel):
    """Модальное окно для Добавления/Редактирования"""

    def __init__(self, parent, title, patient_data=None, on_save=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x450")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.on_save = on_save

        self.entries = {}
        self._build_ui(patient_data)

        self.transient(parent)
        self.grab_set()

    def _build_ui(self, data):
        fields = [
            ("ФИО", "text"),
            ("Возраст", "int"),
            ("Пол", "combo", ["М", "Ж"]),
            ("Рост (см)", "float"),
            ("Вес (кг)", "float"),
        ]

        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        for i, field in enumerate(fields):
            label_text = field[0]
            ftype = field[1]

            tk.Label(
                frame, text=label_text, font=FONT_BOLD, bg=COLORS["bg"], anchor="w"
            ).pack(fill="x", pady=(10, 5))

            if ftype == "combo":
                widget = ttk.Combobox(
                    frame, values=field[2], state="readonly", font=FONT_MAIN
                )
            else:
                widget = tk.Entry(
                    frame, font=FONT_MAIN, bg=COLORS["bg_alt"], bd=1, relief="solid"
                )

            widget.pack(fill="x")

            key = self._get_key_by_label(label_text)
            if data and key in data:
                if ftype == "combo":
                    widget.set(data[key])
                else:
                    widget.insert(0, data[key])

            self.entries[key] = (widget, ftype)

        btn_save = tk.Button(
            frame,
            text="Сохранить",
            bg=COLORS["primary"],
            fg="white",
            font=FONT_BOLD,
            relief="flat",
            command=self._save,
            cursor="hand2",
        )
        btn_save.pack(fill="x", pady=30, ipady=5)

    def _get_key_by_label(self, label):
        mapping = {
            "ФИО": "name",
            "Возраст": "age",
            "Пол": "gender",
            "Рост (см)": "height",
            "Вес (кг)": "weight",
        }
        return mapping.get(label)

    def _save(self):
        result = {}
        try:
            for key, (widget, ftype) in self.entries.items():
                val = widget.get()
                if not val:
                    raise ValueError(f"Поле {key} пустое")

                if ftype == "int":
                    result[key] = int(val)
                elif ftype == "float":
                    result[key] = float(val)
                else:
                    result[key] = val

            if self.on_save:
                self.on_save(result)
            self.destroy()
        except ValueError as e:
            messagebox.showerror(
                "Ошибка валидации", "Проверьте правильность введенных чисел."
            )


class StatsWindow(tk.Toplevel):
    """Окно с графиками matplotlib"""

    def __init__(self, parent, stats_data):
        super().__init__(parent)
        self.title("Сводная статистика")
        self.geometry("900x700")
        self.configure(bg=COLORS["bg"])

        if not stats_data:
            tk.Label(self, text="Нет данных для отображения").pack()
            return

        self._draw_charts(stats_data)

    def _draw_charts(self, data):
        fig, axs = plt.subplots(2, 2, figsize=(8, 6))
        fig.subplots_adjust(hspace=0.4, wspace=0.3)

        # 1. Распределение по полу (Pie Chart)
        m_count = data["genders"].count("М")
        f_count = data["genders"].count("Ж")
        axs[0, 0].pie(
            [m_count, f_count],
            labels=["М", "Ж"],
            autopct="%1.1f%%",
            colors=["#3498db", "#e74c3c"],
        )
        axs[0, 0].set_title("Распределение по полу")

        # 2. Распределение по возрасту (Histogram)
        axs[0, 1].hist(data["ages"], bins=5, color="#2ecc71", edgecolor="black")
        axs[0, 1].set_title("Возрастная структура")
        axs[0, 1].set_xlabel("Лет")

        # 3. ИМТ с учетом пола (Boxplot)
        bmi_m, bmi_f = data["bmi_by_sex"]
        axs[1, 0].boxplot([bmi_m, bmi_f], tick_labels=["М", "Ж"])
        axs[1, 0].set_title("ИМТ по полу")
        axs[1, 0].set_ylabel("BMI")

        # 4. Зависимость ИМТ от возраста (Scatter)
        axs[1, 1].scatter(data["ages"], data["bmis"], color="#9b59b6", alpha=0.7)
        axs[1, 1].set_title("ИМТ vs Возраст")
        axs[1, 1].set_xlabel("Возраст")
        axs[1, 1].set_ylabel("BMI")

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Patient Tracker Pro")
        self.geometry("900x550")
        self.configure(bg=COLORS["bg"])

        self.manager = PatientManager()
        self._setup_styles()
        self._build_ui()
        self._refresh_table()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["bg"],
            rowheight=30,
            font=FONT_MAIN,
        )

        style.configure(
            "Treeview.Heading",
            background=COLORS["primary"],
            foreground=COLORS["header_text"],
            font=FONT_BOLD,
            relief="flat",
        )

        style.map("Treeview.Heading", background=[("active", COLORS["primary_hover"])])

    def _build_ui(self):
        toolbar = tk.Frame(self, bg=COLORS["bg_alt"], height=50)
        toolbar.pack(fill="x", padx=10, pady=10)

        self._create_btn(
            toolbar, "+ Добавить", self._action_add, COLORS["primary"]
        ).pack(side="left", padx=5)
        self._create_btn(toolbar, "✎ Редактировать", self._action_edit, "#FF9500").pack(
            side="left", padx=5
        )

        self._create_btn(
            toolbar, "🗑 Удалить", self._action_delete, COLORS["danger"]
        ).pack(side="left", padx=5)

        self._create_btn(toolbar, "📊 Статистика", self._action_stats, "#5856D6").pack(
            side="right", padx=5
        )

        columns = ("name", "age", "gender", "height", "weight", "bmi")
        headers = ("ФИО", "Возраст", "Пол", "Рост", "Вес", "ИМТ")

        tree_frame = tk.Frame(self)
        tree_frame.pack(expand=True, fill="both", padx=15, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set
        )

        for col, name in zip(columns, headers):
            self.tree.heading(col, text=name, anchor="w")
            self.tree.column(col, width=100 if col != "name" else 250)

        self.tree.pack(expand=True, fill="both")
        scrollbar.config(command=self.tree.yview)

        self.tree.tag_configure("odd", background=COLORS["bg"])
        self.tree.tag_configure("even", background=COLORS["bg_alt"])

    def _create_btn(self, parent, text, cmd, bg_color):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=bg_color,
            fg="white",
            font=FONT_BOLD,
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
        )

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, p in enumerate(self.manager.patients):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "",
                "end",
                iid=i,
                values=(
                    p["name"],
                    p["age"],
                    p["gender"],
                    p["height"],
                    p["weight"],
                    p["bmi"],
                ),
                tags=(tag,),
            )

    def _action_add(self):
        def save_handler(data):
            self.manager.add_patient(data)
            self._refresh_table()

        PatientForm(self, "Новый пациент", on_save=save_handler)

    def _action_edit(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пациента для редактирования")
            return

        idx = int(selected[0])
        data = self.manager.patients[idx]

        def update_handler(new_data):
            self.manager.update_patient(idx, new_data)
            self._refresh_table()

        PatientForm(self, "Редактирование", patient_data=data, on_save=update_handler)

    def _action_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пациента для удаления")
            return

        idx = int(selected[0])
        patient_name = self.manager.patients[idx]["name"]

        if messagebox.askyesno(
            "Подтверждение",
            f"Вы уверены, что хотите удалить пациента '{patient_name}'?",
        ):
            self.manager.delete_patient(idx)
            self._refresh_table()
            messagebox.showinfo("Успех", f"Пациент '{patient_name}' удален.")

    def _action_stats(self):
        stats = self.manager.get_stats()
        if not stats:
            messagebox.showinfo("Инфо", "Нет данных для статистики")
            return
        StatsWindow(self, stats)


if __name__ == "__main__":
    app = App()
    app.mainloop()
