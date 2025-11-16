import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import os
import subprocess
import shlex


YAML_PATH = "pandoc_options.yaml"


class PandocGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pandoc GUI — динамически из YAML")
        self.root.geometry("1000x900")
        self.root.minsize(900, 600)

        try:
            with open(YAML_PATH, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл {YAML_PATH} не найден!")
            root.destroy()
            return
        if not self.config or "options" not in self.config:
            messagebox.showerror("Ошибка", "Неверный формат YAML: нужен ключ 'options'")
            root.destroy()
            return

        self.options = self.config["options"]
        self.vars = {}
        self.manual_edit = False
        self.pending_from = None

        # Уникальные уровни популярности
        self.popularity_levels = sorted({opt.get("popularity", 0) for opt in self.options}, reverse=True)
        self.popularity_levels = [lvl for lvl in self.popularity_levels if isinstance(lvl, int) and lvl > 0]
        if not self.popularity_levels:
            self.popularity_levels = [1, 2, 3, 4, 5]

        self.popularity_threshold = 4

        self.create_widgets()
        self.update_command()

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # === Выбор файла + фильтр популярности ===
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(top_frame, text="Входной файл:", width=15, anchor="w").pack(side="left")
        self.input_file_var = tk.StringVar()
        tk.Entry(top_frame, textvariable=self.input_file_var, width=60).pack(side="left", padx=5)
        tk.Button(top_frame, text="Обзор...", command=self.browse_input).pack(side="left", padx=(5, 20))

        tk.Label(top_frame, text="Показывать параметры (популярность ≥):", width=35, anchor="w").pack(side="left")
        self.pop_filter_var = tk.StringVar(value="4")
        pop_combo = ttk.Combobox(top_frame, textvariable=self.pop_filter_var, values=self.popularity_levels, state="readonly", width=5)
        pop_combo.pack(side="left")
        pop_combo.bind("<<ComboboxSelected>>", self.on_popularity_filter_change)

        # === Итоговая команда (редактируемая, с переносом) ===
        cmd_frame = tk.LabelFrame(main_frame, text="Итоговая команда pandoc (можно редактировать)", padx=10, pady=5)
        cmd_frame.pack(fill="x", padx=10, pady=5)
        self.cmd_text = tk.Text(
            cmd_frame,
            height=4,
            font=("Courier New", 10),
            wrap="word"
        )
        self.cmd_text.pack(fill="x")
        self.cmd_text.bind("<Key>", self.on_manual_edit)

        # === Прокручиваемая область параметров ===
        scroll_frame = tk.Frame(main_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        canvas = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self.redraw_options()

        # === Кнопка конвертации ===
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Конвертировать", command=self.run_pandoc,
                  bg="#4CAF50", fg="white", height=2, font=("TkDefaultFont", 10, "bold")).pack()

    def on_popularity_filter_change(self, event=None):
        try:
            self.popularity_threshold = int(self.pop_filter_var.get())
        except:
            self.popularity_threshold = 4
        self.redraw_options()

    def on_manual_edit(self, event=None):
        self.manual_edit = True

    def on_option_change(self, *args):
        self.manual_edit = False
        self.update_command()

    def redraw_options(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.vars.clear()

        filtered_opts = [
            opt for opt in self.options
            if opt.get("popularity", 0) >= self.popularity_threshold
        ]

        categories = {}
        for opt in filtered_opts:
            cat = opt.get("category", "general")
            categories.setdefault(cat, []).append(opt)

        for cat in sorted(categories):
            cat_frame = tk.LabelFrame(self.scrollable_frame, text=f"Категория: {cat}", padx=10, pady=10)
            cat_frame.pack(fill="x", padx=5, pady=5)
            for opt in categories[cat]:
                self.create_option_widget(cat_frame, opt)

    def create_option_widget(self, parent, opt):
        name = opt["name"]
        gui_hint = opt.get("gui_hint", "entry")
        desc = opt.get("description", "")
        default = opt.get("default", None)

        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=3)

        var = self.create_variable(opt, default)
        self.vars[name] = var

        # Применяем отложенное значение для 'from'
        if name == "from" and self.pending_from is not None:
            var.set(self.pending_from)
            self.pending_from = None

        label_text = f"{name}:"
        if opt.get("cli"):
            label_text = f"{opt['cli'][-1]} ({name}):"
        tk.Label(frame, text=label_text, width=30, anchor="w").pack(side="left")

        if gui_hint == "checkbox":
            widget = tk.Checkbutton(frame, variable=var)
            widget.pack(side="left")
        elif gui_hint == "combobox":
            choices = opt.get("choices", opt.get("choices_from", []))
            if isinstance(choices, str):
                if choices == "input_formats":
                    choices = self.get_input_formats()
                elif choices == "output_formats":
                    choices = self.get_output_formats()
            widget = ttk.Combobox(frame, textvariable=var, values=choices, state="readonly", width=25)
            widget.pack(side="left")
        else:
            widget = tk.Entry(frame, textvariable=var, width=35)
            widget.pack(side="left")

        if desc:
            tk.Label(frame, text=desc, fg="gray", wraplength=500, justify="left").pack(padx=(10, 0), pady=(2, 0), anchor="w")

        if hasattr(var, "trace_add"):
            var.trace_add("write", self.on_option_change)

    def create_variable(self, opt, default):
        otype = opt.get("type", "string")
        if otype == "boolean":
            return tk.BooleanVar(value=bool(default))
        else:
            return tk.StringVar(value=str(default) if default is not None else "")

    def get_input_formats(self):
        try:
            res = subprocess.run(["pandoc", "--list-input-formats"], capture_output=True, text=True, check=True)
            return sorted(res.stdout.strip().split())
        except:
            return ["markdown", "html", "latex", "docx"]

    def get_output_formats(self):
        try:
            res = subprocess.run(["pandoc", "--list-output-formats"], capture_output=True, text=True, check=True)
            return sorted(res.stdout.strip().split())
        except:
            return ["html", "latex", "pdf", "docx", "markdown"]

    def browse_input(self):
        f = filedialog.askopenfilename()
        if f:
            self.input_file_var.set(f)
            self.auto_set_from_format(f)
            self.manual_edit = False
            self.update_command()

    def auto_set_from_format(self, filepath):
        _, ext = os.path.splitext(filepath)
        ext = ext.lower().lstrip('.')

        ext_to_format = {
            'md': 'markdown',
            'markdown': 'markdown',
            'mkd': 'markdown',
            'mdown': 'markdown',
            'html': 'html',
            'htm': 'html',
            'xml': 'html',
            'txt': 'markdown',
            'tex': 'latex',
            'latex': 'latex',
            'ltx': 'latex',
            'docx': 'docx',
            'odt': 'odt',
            'rtf': 'rtf',
            'epub': 'epub',
            'json': 'json',
            'ipynb': 'ipynb',
            'org': 'org',
            'rst': 'rst',
            'textile': 'textile',
            'opml': 'opml',
            't2t': 't2t',
            'ms': 'ms',
            'man': 'man',
        }

        fmt = ext_to_format.get(ext, 'auto')

        if 'from' in self.vars:
            self.vars['from'].set(fmt)
        else:
            self.pending_from = fmt

    def get_current_values(self):
        vals = {"input_file": self.input_file_var.get()}
        for name, var in self.vars.items():
            opt = next((o for o in self.options if o["name"] == name), None)
            if not opt:
                continue
            raw = var.get()
            otype = opt.get("type", "string")
            if otype == "boolean":
                vals[name] = var.get()
            else:
                vals[name] = raw
        return vals

    def build_command(self, vals):
        cmd = ["pandoc"]
        inp = vals.get("input_file")
        if inp:
            cmd.append(inp)

        for opt in self.options:
            if opt.get("popularity", 0) < self.popularity_threshold:
                continue
            name = opt["name"]
            cli = opt.get("cli", [])
            if not cli:
                continue
            value = vals.get(name)
            otype = opt.get("type", "string")

            if otype == "boolean":
                if value:
                    cmd.append(cli[-1])
            else:
                if value is not None and value != "":
                    if name == "wrap" and value == "auto":
                        continue
                    cmd.append(cli[-1])
                    cmd.append(str(value))

        # Динамический выходной файл
        if inp:
            to_fmt = vals.get("to", "markdown")
            base = os.path.splitext(inp)[0]
            ext_map = {
                "pdf": ".pdf", "docx": ".docx", "odt": ".odt", "epub": ".epub",
                "html": ".html", "html5": ".html", "latex": ".tex", "beamer": ".tex",
                "markdown": ".md", "gfm": ".md", "commonmark": ".md", "plain": ".txt",
                "json": ".json", "rst": ".rst", "org": ".org", "opml": ".opml",
                "xml": ".xml", "man": ".1", "mediawiki": ".wiki", "dokuwiki": ".dokuwiki"
            }
            ext = ext_map.get(to_fmt, "." + to_fmt)
            out_file = base + ext
            cmd.extend(["-o", out_file])

        def quote(s):
            return f'"{s}"' if any(c in s for c in " \t\n\r\"'") else s
        return " ".join(quote(part) for part in cmd)

    def update_command(self, *args):
        if self.manual_edit:
            return
        vals = self.get_current_values()
        cmd = self.build_command(vals)
        self.cmd_text.delete("1.0", tk.END)
        self.cmd_text.insert("1.0", cmd)

    def run_pandoc(self):
        raw_cmd = self.cmd_text.get("1.0", tk.END).strip()
        if not raw_cmd:
            messagebox.showerror("Ошибка", "Команда пуста!")
            return

        try:
            cmd_list = shlex.split(raw_cmd)
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный синтаксис команды:\n{e}")
            return

        if not cmd_list or cmd_list[0] != "pandoc":
            messagebox.showerror("Ошибка", "Команда должна начинаться с 'pandoc'")
            return

        try:
            subprocess.run(cmd_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "-o" in cmd_list:
                try:
                    idx = cmd_list.index("-o")
                    out_file = cmd_list[idx + 1]
                    messagebox.showinfo("Успех", f"Файл создан:\n{os.path.abspath(out_file)}")
                except (IndexError, ValueError):
                    messagebox.showinfo("Успех", "Команда выполнена (без -o).")
            else:
                messagebox.showinfo("Успех", "Команда выполнена. Результат в stdout.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка Pandoc", e.stderr[:1000])
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "Pandoc не найден. Установите его и добавьте в PATH.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PandocGUI(root)
    root.mainloop()