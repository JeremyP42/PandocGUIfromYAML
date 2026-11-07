import ctypes
import os
import re
import shlex
import shutil
import subprocess
import sys

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import yaml


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(SCRIPT_DIR, "pandoc_options.yaml")
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

DEFAULT_INPUT_FORMATS = ["markdown", "html", "latex", "docx", "rst", "org", "epub", "json", "ipynb"]
DEFAULT_OUTPUT_FORMATS = ["html", "latex", "pdf", "docx", "markdown", "epub", "odt", "rst", "plain"]

EXT_TO_FORMAT = {
    "md": "markdown",
    "markdown": "markdown",
    "mkd": "markdown",
    "mdown": "markdown",
    "html": "html",
    "htm": "html",
    "xml": "html",
    "txt": "markdown",
    "tex": "latex",
    "latex": "latex",
    "ltx": "latex",
    "docx": "docx",
    "odt": "odt",
    "fodt": "fodt",
    "rtf": "rtf",
    "epub": "epub",
    "json": "json",
    "ipynb": "ipynb",
    "org": "org",
    "rst": "rst",
    "textile": "textile",
    "opml": "opml",
    "t2t": "t2t",
    "ms": "ms",
    "man": "man",
    "typ": "typst",
    "typst": "typst",
    "djot": "djot",
    "adoc": "asciidoc",
    "asciidoc": "asciidoc",
    "csv": "csv",
    "tsv": "tsv",
    "bib": "biblatex",
    "ris": "ris",
    "fb2": "fb2",
    "pptx": "pptx",
    "xlsx": "xlsx",
    "muse": "muse",
    "pod": "pod",
}

FORMAT_TO_EXT = {
    "pdf": ".pdf",
    "docx": ".docx",
    "odt": ".odt",
    "fodt": ".fodt",
    "epub": ".epub",
    "epub2": ".epub",
    "epub3": ".epub",
    "html": ".html",
    "html4": ".html",
    "html5": ".html",
    "chunkedhtml": ".html",
    "revealjs": ".html",
    "dzslides": ".html",
    "s5": ".html",
    "slidy": ".html",
    "slideous": ".html",
    "latex": ".tex",
    "beamer": ".tex",
    "context": ".tex",
    "markdown": ".md",
    "gfm": ".md",
    "commonmark": ".md",
    "commonmark_x": ".md",
    "markdown_strict": ".md",
    "markdown_mmd": ".md",
    "markdown_phpextra": ".md",
    "markua": ".md",
    "plain": ".txt",
    "ansi": ".txt",
    "bbcode": ".txt",
    "json": ".json",
    "csljson": ".json",
    "bibtex": ".bib",
    "biblatex": ".bib",
    "rst": ".rst",
    "org": ".org",
    "opml": ".opml",
    "xml": ".xml",
    "jats": ".xml",
    "docbook": ".xml",
    "docbook4": ".xml",
    "docbook5": ".xml",
    "tei": ".tei",
    "man": ".1",
    "ms": ".ms",
    "typst": ".typ",
    "ipynb": ".ipynb",
    "native": ".native",
    "pptx": ".pptx",
    "mediawiki": ".wiki",
    "dokuwiki": ".dokuwiki",
    "xwiki": ".xwiki",
    "zimwiki": ".zimwiki",
    "jira": ".txt",
    "t2t": ".t2t",
    "textile": ".textile",
    "texinfo": ".texi",
    "icml": ".icml",
}


def run_capture(executable, args):
    return subprocess.run(
        [executable] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=CREATE_NO_WINDOW,
    )


def find_pandoc_candidates():
    names = ["pandoc.exe", "pandoc"] if os.name == "nt" else ["pandoc"]
    candidates = []

    env_path = os.environ.get("PANDOC", "").strip()
    if env_path:
        candidates.append(env_path)

    for name in names:
        candidates.append(os.path.join(SCRIPT_DIR, name))

    for name in names:
        found = shutil.which(name)
        if found:
            candidates.append(found)

    if os.name == "nt":
        roots = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        for root in roots:
            if root:
                candidates.append(os.path.join(root, "Pandoc", "pandoc.exe"))
                candidates.append(os.path.join(root, "pandoc", "pandoc.exe"))

    result = []
    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        path = os.path.abspath(candidate)
        key = os.path.normcase(path)
        if key in seen or not os.path.isfile(path):
            continue
        seen.add(key)
        result.append(path)
    return result


def probe_pandoc(path):
    try:
        version_res = run_capture(path, ["--version"])
    except OSError:
        return None
    if version_res.returncode != 0:
        return None

    first_line = (version_res.stdout or "").splitlines()[:1]
    version = ""
    if first_line:
        match = re.search(r"\d+(?:\.\d+)+(?:\.\d+)?", first_line[0])
        version = match.group(0) if match else first_line[0].strip()

    try:
        help_res = run_capture(path, ["--help"])
        help_text = help_res.stdout or ""
    except OSError:
        help_text = ""

    return version, help_text


def supported_flags(help_text):
    return set(re.findall(r"--[A-Za-z0-9][A-Za-z0-9-]*", help_text))


def split_command_line(text):
    if os.name == "nt":
        try:
            from ctypes import wintypes

            shell32 = ctypes.windll.shell32
            shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
            shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
            argc = ctypes.c_int(0)
            argv = shell32.CommandLineToArgvW(text, ctypes.byref(argc))
            if not argv:
                raise ValueError("не удалось разобрать командную строку")
            try:
                return [argv[index] for index in range(argc.value)]
            finally:
                ctypes.windll.kernel32.LocalFree(argv)
        except OSError:
            pass
    return shlex.split(text)


def format_command(argv):
    if not argv:
        return ""
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return " ".join(shlex.quote(part) for part in argv)


class PandocGUI:
    def __init__(self, root):
        self.root = root
        self.failed = False
        self.root.title("Pandoc GUI — динамически из YAML")
        self.root.geometry("1000x900")
        self.root.minsize(900, 600)

        try:
            with open(YAML_PATH, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.failed = True
            messagebox.showerror("Ошибка", f"Файл {YAML_PATH} не найден!")
            root.destroy()
            return
        except Exception as exc:
            self.failed = True
            messagebox.showerror("Ошибка", f"Не удалось прочитать {YAML_PATH}:\n{exc}")
            root.destroy()
            return

        if not self.config or "options" not in self.config:
            self.failed = True
            messagebox.showerror("Ошибка", "Неверный формат YAML: нужен ключ 'options'")
            root.destroy()
            return

        self.options = self.deduplicate_options(self.config["options"])
        self.vars = {}
        self.manual_edit = False
        self.pending_from = None

        self.pandoc_exe = None
        self.pandoc_version = ""
        self.unsupported = {}
        self.input_formats = ["auto"] + list(DEFAULT_INPUT_FORMATS)
        self.output_formats = list(DEFAULT_OUTPUT_FORMATS)
        self.last_argv = []
        self.last_display = None
        self.status_var = None

        self.detect_pandoc()

        # Уникальные уровни популярности
        self.popularity_levels = sorted({opt.get("popularity", 0) for opt in self.options}, reverse=True)
        self.popularity_levels = [lvl for lvl in self.popularity_levels if isinstance(lvl, int) and lvl > 0]
        if not self.popularity_levels:
            self.popularity_levels = [1, 2, 3, 4, 5]

        self.popularity_threshold = 4

        self.create_widgets()
        self.update_status()
        self.update_command()

        if not self.pandoc_exe:
            messagebox.showwarning(
                "Pandoc не найден",
                "Pandoc не найден ни рядом со скриптом, ни в PATH.\n\n"
                "Запустите 1_pandoc_download.bat (положит pandoc.exe рядом со скриптом) "
                "или установите Pandoc в систему.",
            )

    @staticmethod
    def deduplicate_options(options):
        unique = []
        seen = set()
        for opt in options:
            if not isinstance(opt, dict) or "name" not in opt:
                continue
            name = opt["name"]
            if name in seen:
                continue
            seen.add(name)
            unique.append(opt)
        return unique

    def detect_pandoc(self):
        for candidate in find_pandoc_candidates():
            probed = probe_pandoc(candidate)
            if not probed:
                continue
            self.pandoc_exe = candidate
            self.pandoc_version, help_text = probed
            self.unsupported = self.collect_unsupported(supported_flags(help_text))
            break

        if self.pandoc_exe:
            self.input_formats = ["auto"] + self.fetch_formats("--list-input-formats", DEFAULT_INPUT_FORMATS)
            self.output_formats = self.fetch_formats("--list-output-formats", DEFAULT_OUTPUT_FORMATS)
            if self.pandoc_version:
                self.root.title(f"Pandoc GUI — динамически из YAML (pandoc {self.pandoc_version})")

    def collect_unsupported(self, flags):
        unsupported = {}
        for opt in self.options:
            long_flags = [flag for flag in (opt.get("cli") or []) if flag.startswith("--")]
            if long_flags and not any(flag in flags for flag in long_flags):
                unsupported[opt["name"]] = " ".join(long_flags)
        return unsupported

    def fetch_formats(self, argument, fallback):
        if not self.pandoc_exe:
            return list(fallback)
        try:
            result = run_capture(self.pandoc_exe, [argument])
        except OSError:
            return list(fallback)
        if result.returncode != 0:
            return list(fallback)
        formats = sorted({line.strip() for line in (result.stdout or "").splitlines() if line.strip()})
        return formats or list(fallback)

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

        self.status_var = tk.StringVar(value="")
        tk.Label(main_frame, textvariable=self.status_var, fg="gray", anchor="w", justify="left",
                 wraplength=960).pack(fill="x", padx=10, pady=(0, 8))

    def update_status(self):
        if self.status_var is None:
            return
        parts = []
        if self.pandoc_exe:
            parts.append(f"pandoc {self.pandoc_version} — {self.pandoc_exe}")
        else:
            parts.append("pandoc не найден: запустите 1_pandoc_download.bat")
        if self.unsupported:
            hidden = ", ".join(sorted(self.unsupported))
            parts.append(f"скрыто параметров, не поддерживаемых этой версией pandoc: {len(self.unsupported)} ({hidden})")
        self.status_var.set("   |   ".join(parts))

    def on_popularity_filter_change(self, event=None):
        try:
            self.popularity_threshold = int(self.pop_filter_var.get())
        except Exception:
            self.popularity_threshold = 4
        self.redraw_options()
        self.update_command()

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
            and opt["name"] not in self.unsupported
        ]

        if not filtered_opts:
            tk.Label(
                self.scrollable_frame,
                text="Нет параметров с такой популярностью, поддерживаемых установленной версией pandoc.",
                fg="gray",
            ).pack(padx=10, pady=10, anchor="w")
            return

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
        elif gui_hint in ("combobox", "editable_combobox"):
            choices = opt.get("choices", opt.get("choices_from", []))
            if isinstance(choices, str):
                if choices == "input_formats":
                    choices = self.get_input_formats()
                elif choices == "output_formats":
                    choices = self.get_output_formats()
            combo_state = "readonly" if gui_hint == "combobox" else "normal"
            widget = ttk.Combobox(frame, textvariable=var, values=choices, state=combo_state, width=25)
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
        if default is None or isinstance(default, (dict, list)):
            return tk.StringVar(value="")
        return tk.StringVar(value=str(default))

    def get_input_formats(self):
        return list(self.input_formats)

    def get_output_formats(self):
        return list(self.output_formats)

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

        fmt = EXT_TO_FORMAT.get(ext, 'auto')

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
            if opt.get("type", "string") == "boolean":
                vals[name] = var.get()
            else:
                vals[name] = var.get()
        return vals

    def default_output_path(self, inp, to_fmt):
        base = os.path.splitext(inp)[0]
        ext = FORMAT_TO_EXT.get(to_fmt) or ("." + to_fmt if to_fmt else ".out")
        out_file = base + ext
        if os.path.normcase(os.path.abspath(out_file)) == os.path.normcase(os.path.abspath(inp)):
            out_file = base + "_converted" + ext
        return out_file

    def build_argv(self, vals):
        cmd = [self.pandoc_exe or "pandoc"]
        inp = vals.get("input_file")
        if inp:
            cmd.append(inp)

        for opt in self.options:
            if opt.get("popularity", 0) < self.popularity_threshold:
                continue
            name = opt["name"]
            cli = opt.get("cli") or []
            if not cli or name in self.unsupported or name == "output":
                continue
            value = vals.get(name)
            otype = opt.get("type", "string")

            if otype == "boolean":
                if value:
                    cmd.append(cli[-1])
                continue

            if value is None:
                continue
            value = str(value).strip()
            if not value:
                continue
            if name == "from" and value.lower() in ("auto", "none"):
                continue
            flag = cli[-1]
            if flag.startswith("--"):
                cmd.append(f"{flag}={value}")
            else:
                cmd.append(flag)
                cmd.append(value)

        to_fmt = str(vals.get("to") or "markdown").strip()
        out_file = str(vals.get("output") or "").strip()
        if not out_file and inp:
            out_file = self.default_output_path(inp, to_fmt)
        if out_file:
            cmd.append("--output=" + out_file)

        return cmd

    def update_command(self, *args):
        if self.manual_edit:
            return
        vals = self.get_current_values()
        argv = self.build_argv(vals)
        display_argv = ["pandoc"] + argv[1:]
        self.last_argv = argv
        self.last_display = format_command(display_argv)
        self.cmd_text.delete("1.0", tk.END)
        self.cmd_text.insert("1.0", self.last_display)

    def run_pandoc(self):
        raw_cmd = self.cmd_text.get("1.0", tk.END).strip()
        if not raw_cmd:
            messagebox.showerror("Ошибка", "Команда пуста!")
            return

        if self.last_display is not None and raw_cmd == self.last_display:
            cmd_list = list(self.last_argv)
        else:
            try:
                cmd_list = split_command_line(raw_cmd)
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверный синтаксис команды:\n{e}")
                return

        if not cmd_list:
            messagebox.showerror("Ошибка", "Команда пуста!")
            return

        program = os.path.basename(cmd_list[0]).lower()
        if not program.startswith("pandoc"):
            messagebox.showerror("Ошибка", "Команда должна начинаться с 'pandoc'")
            return

        if not self.pandoc_exe:
            messagebox.showerror(
                "Pandoc не найден",
                "Не удалось найти pandoc.\nЗапустите 1_pandoc_download.bat "
                "или установите Pandoc и добавьте его в PATH.",
            )
            return

        cmd_list[0] = self.pandoc_exe

        try:
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
            )
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "Pandoc не найден. Установите его и добавьте в PATH.")
            return
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить pandoc:\n{e}")
            return

        if result.returncode != 0:
            messagebox.showerror(
                "Ошибка Pandoc",
                (result.stderr or result.stdout or f"Код возврата {result.returncode}").strip()[:2000],
            )
            return

        out_file = self.find_output_file(cmd_list)
        if out_file:
            message = f"Файл создан:\n{os.path.abspath(out_file)}"
        else:
            message = "Команда выполнена. Результат в stdout."

        warnings = (result.stderr or "").strip()
        if warnings:
            message += "\n\nПредупреждения:\n" + warnings[:1200]
        messagebox.showinfo("Успех", message)

    @staticmethod
    def find_output_file(cmd_list):
        for index, part in enumerate(cmd_list):
            if part in ("-o", "--output"):
                if index + 1 < len(cmd_list):
                    return cmd_list[index + 1]
            elif part.startswith("--output="):
                return part.split("=", 1)[1]
        return None


if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = PandocGUI(root)
    except Exception:
        import traceback
        messagebox.showerror("Ошибка запуска", traceback.format_exc()[:2000])
        root.destroy()
        sys.exit(1)
    if app.failed:
        sys.exit(1)
    root.mainloop()
