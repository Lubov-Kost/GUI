import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pathlib import Path

from fastq_reader import FastqReader

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    HAS_DND = True
    BaseClass = TkinterDnD.Tk
except ImportError:
    HAS_DND = False
    BaseClass = tk.Tk

COLORS = {
    "bg": "#FFFFFF",
    "primary": "#007AFF",
    "secondary": "#F2F2F7",
    "text": "#333333",
    "success": "#34C759",
    "danger": "#FF3B30",
}


class FastqAnalyzerApp(BaseClass):
    def __init__(self):
        super().__init__()
        self.title("BioStats: FASTQ Analyzer")
        self.geometry("1000x750")
        self.configure(bg=COLORS["bg"])

        self.current_file = None
        self.is_processing = False

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10))

        style.configure("Horizontal.TProgressbar", background=COLORS["primary"])

    def _build_ui(self):
        top_frame = tk.Frame(self, bg=COLORS["secondary"], height=100, padx=20, pady=20)
        top_frame.pack(fill="x")

        lbl_title = tk.Label(
            top_frame,
            text="FASTQ Reader UI",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["secondary"],
            fg=COLORS["text"],
        )
        lbl_title.pack(anchor="w")

        file_frame = tk.Frame(top_frame, bg=COLORS["secondary"])
        file_frame.pack(fill="x", pady=(10, 0))

        self.btn_select = tk.Button(
            file_frame,
            text="📂 Выбрать файл...",
            command=self._select_file_dialog,
            bg=COLORS["primary"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
        )
        self.btn_select.pack(side="left")

        self.lbl_filename = tk.Label(
            file_frame,
            text="Файл не выбран",
            font=("Segoe UI", 10),
            bg=COLORS["secondary"],
            fg="#666",
        )
        self.lbl_filename.pack(side="left", padx=15)

        if HAS_DND:
            self.drop_area = tk.Label(
                top_frame,
                text="...или перетащите файл сюда",
                bg="#E1E1E6",
                fg="#888",
                relief="groove",
                bd=2,
            )
            self.drop_area.place(relx=0.7, rely=0.1, relwidth=0.28, relheight=0.8)

            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self._on_drop)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.tab_summary = ttk.Frame(self.notebook)
        self.tab_len_dist = ttk.Frame(self.notebook)
        self.tab_quality = ttk.Frame(self.notebook)
        self.tab_content = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_summary, text="📝 Сводка")
        self.notebook.add(self.tab_len_dist, text="📏 Длины ридов")
        self.notebook.add(self.tab_quality, text="⭐ Качество (Phred)")
        self.notebook.add(self.tab_content, text="🧬 Состав (ACGT)")

        for tab in [self.tab_len_dist, self.tab_quality, self.tab_content]:
            tk.Label(
                tab, text="Загрузите файл для построения графика", bg=COLORS["bg"]
            ).pack(expand=True)

        self.txt_summary = tk.Text(
            self.tab_summary, font=("Consolas", 11), padx=10, pady=10, state="disabled"
        )
        self.txt_summary.pack(expand=True, fill="both")

        status_frame = tk.Frame(self, bg=COLORS["bg"], height=30)
        status_frame.pack(fill="x", side="bottom")

        self.progress = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress.pack(fill="x", padx=0, pady=0)

    def _select_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Выберите FASTQ файл",
            filetypes=[("FASTQ files", "*.fastq *.fq *.gz"), ("All files", "*.*")],
        )
        if file_path:
            self._start_analysis(file_path)

    def _on_drop(self, event):
        file_path = event.data
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        self._start_analysis(file_path)

    def _start_analysis(self, file_path):
        if self.is_processing:
            return

        path_obj = Path(file_path)
        if not path_obj.exists():
            messagebox.showerror("Ошибка", "Файл не существует!")
            return

        self.current_file = path_obj
        self.lbl_filename.config(text=f"Файл: {path_obj.name}", fg=COLORS["text"])

        self.is_processing = True
        self.btn_select.config(state="disabled")
        self.progress.start(10)
        self.txt_summary.config(state="normal")
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert(
            "1.0",
            "Анализ файла...\nПожалуйста, подождите. Для больших файлов это может занять время.",
        )
        self.txt_summary.config(state="disabled")

        self._clear_tab(self.tab_len_dist)
        self._clear_tab(self.tab_quality)
        self._clear_tab(self.tab_content)

        threading.Thread(
            target=self._worker_analyze, args=(path_obj,), daemon=True
        ).start()

    def _worker_analyze(self, file_path):
        """Фоновая задача для парсинга и сбора статистики."""
        try:
            sequence_lengths = []
            quality_per_position = {}
            base_content_per_position = {}

            total_sequences = 0
            total_length = 0
            gc_count = 0
            total_bases_count = 0

            with FastqReader(file_path) as reader:
                for record in reader.read():
                    seq = record.sequence
                    qual = record.quality
                    seq_len = len(seq)

                    total_sequences += 1
                    total_length += seq_len
                    sequence_lengths.append(seq_len)

                    seq_upper = seq.upper()
                    gc_count += seq_upper.count("G") + seq_upper.count("C")
                    total_bases_count += seq_len

                    for i, q in enumerate(qual):
                        if i not in quality_per_position:
                            quality_per_position[i] = []
                        quality_per_position[i].append(q)

                    for i, base in enumerate(seq_upper):
                        if i not in base_content_per_position:
                            base_content_per_position[i] = {
                                "A": 0,
                                "T": 0,
                                "G": 0,
                                "C": 0,
                            }
                        if base in "ATGC":
                            base_content_per_position[i][base] += 1

            stats = {
                "total_seq": total_sequences,
                "avg_len": total_length / total_sequences if total_sequences else 0,
                "gc_content": (
                    (gc_count / total_bases_count * 100) if total_bases_count else 0
                ),
                "seq_lens": sequence_lengths,
                "qual_pos": quality_per_position,
                "base_pos": base_content_per_position,
            }

            self.after(0, self._update_ui_success, stats)

        except Exception as e:
            self.after(0, self._update_ui_error, str(e))

    def _update_ui_error(self, error_msg):
        self.progress.stop()
        self.is_processing = False
        self.btn_select.config(state="normal")
        messagebox.showerror(
            "Ошибка анализа", f"Не удалось прочитать файл:\n{error_msg}"
        )

    def _update_ui_success(self, stats):
        self.progress.stop()
        self.is_processing = False
        self.btn_select.config(state="normal")

        summary_text = (
            f"РЕЗУЛЬТАТЫ АНАЛИЗА\n"
            f"==================\n"
            f"Файл: {self.current_file.name}\n\n"
            f"Всего последовательностей: {stats['total_seq']:,}\n"
            f"Средняя длина:             {stats['avg_len']:.2f} bp\n"
            f"GC состав:                 {stats['gc_content']:.2f} %\n"
        )
        self.txt_summary.config(state="normal")
        self.txt_summary.delete("1.0", tk.END)
        self.txt_summary.insert("1.0", summary_text)
        self.txt_summary.config(state="disabled")

        self._plot_length_distribution(stats["seq_lens"])
        self._plot_quality(stats["qual_pos"])
        self._plot_content(stats["base_pos"])

    def _clear_tab(self, tab):
        for widget in tab.winfo_children():
            widget.destroy()

    def _embed_matplotlib(self, fig, parent_tab):
        """Встраивает фигуру Matplotlib в Tkinter Frame."""
        canvas = FigureCanvasTkAgg(fig, master=parent_tab)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, parent_tab)
        toolbar.update()

        canvas.get_tk_widget().pack(expand=True, fill="both")

    def _plot_length_distribution(self, lengths):
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        if lengths:
            bins = min(50, len(set(lengths)))
            ax.hist(lengths, bins=bins, color="skyblue", edgecolor="black", alpha=0.7)
            ax.set_title("Sequence Length Distribution")
            ax.set_xlabel("Length (bp)")
            ax.set_ylabel("Count")
            ax.grid(True, linestyle="--", alpha=0.3)
        else:
            ax.text(0.5, 0.5, "No Data", ha="center")

        self._embed_matplotlib(fig, self.tab_len_dist)

    def _plot_quality(self, qual_data):
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        if qual_data:
            positions = sorted(qual_data.keys())
            mean_qualities = [sum(qual_data[p]) / len(qual_data[p]) for p in positions]

            ax.plot(positions, mean_qualities, color="#007AFF", linewidth=2)
            ax.axhline(y=20, color="#FF3B30", linestyle="--", alpha=0.5, label="Q20")
            ax.axhline(y=30, color="#34C759", linestyle="--", alpha=0.5, label="Q30")

            ax.set_title("Mean Quality per Position")
            ax.set_xlabel("Position (bp)")
            ax.set_ylabel("Phred Score")
            ax.legend()
            ax.grid(True, linestyle="--", alpha=0.3)
        else:
            ax.text(0.5, 0.5, "No Data", ha="center")

        self._embed_matplotlib(fig, self.tab_quality)

    def _plot_content(self, base_data):
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        if base_data:
            positions = sorted(base_data.keys())
            a, t, g, c = [], [], [], []

            for p in positions:
                total = sum(base_data[p].values())
                if total > 0:
                    a.append(base_data[p]["A"] / total * 100)
                    t.append(base_data[p]["T"] / total * 100)
                    g.append(base_data[p]["G"] / total * 100)
                    c.append(base_data[p]["C"] / total * 100)
                else:
                    a.append(0)
                    t.append(0)
                    g.append(0)
                    c.append(0)

            ax.plot(positions, a, label="A", color="green", alpha=0.8)
            ax.plot(positions, t, label="T", color="red", alpha=0.8)
            ax.plot(positions, g, label="G", color="black", alpha=0.8)
            ax.plot(positions, c, label="C", color="blue", alpha=0.8)

            ax.set_title("Base Content per Position")
            ax.set_ylabel("%")
            ax.set_xlabel("Position")
            ax.legend(loc="upper right")
            ax.set_ylim(0, 100)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, "No Data", ha="center")

        self._embed_matplotlib(fig, self.tab_content)


if __name__ == "__main__":
    app = FastqAnalyzerApp()
    app.mainloop()
