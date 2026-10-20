"""Acá manejo la ventana; solo actualizo Tk desde el hilo principal."""
from __future__ import annotations

import csv
import json
import math
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from .themes import THEMES
from .plotting import GraphView
from .keyboard import MathKeyboard
from .examples import EXAMPLES
from .expressions import Expression, ExpressionError, parse_bound
from .numerics import CalculationError, CancelledError, Result, Settings, calculate

BG = "#eef3f8"
INK = "#152c43"
TEAL = "#087f8c"
MUTED = "#51677c"
PRECISIONS = {"Normal · 1e-6": 1e-6, "Alta · 1e-8": 1e-8, "Muy alta · 1e-10": 1e-10}

def number(value: float) -> str:
    return format(value, ".12g")

def sample_curve(result: Result, count: int = 361) -> list[tuple[float, float | None]]:
    function = Expression.parse(result.expression)
    points = []
    for i in range(count):
        x = result.a if i == 0 else result.b if i == count - 1 else (
            result.a + (result.b - result.a) * i / (count - 1))
        try:
            y = function(x)
        except ExpressionError:
            y = None
        points.append((x, y))
    return points

def export_json(path: str | Path, result: Result) -> None:
    Path(path).write_text(json.dumps(result.to_dict(), ensure_ascii=False,
                                    indent=2, allow_nan=False) + "\n", encoding="utf-8")

def export_csv(path: str | Path, result: Result) -> None:
    with Path(path).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(("x", "f(x)", "valor_promedio"))
        for x, y in sample_curve(result, 501):
            writer.writerow((repr(x), "" if y is None else repr(y), repr(result.average)))

class AverageApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.busy = False
        self.closed = False
        self.result: Result | None = None
        self.history: list[Result] = []
        self.messages: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        root.title("Cálculo del promedio de una función matemática")
        # Reservo espacio para el título y la barra de tareas en pantallas de 768 px.
        height = min(790, max(640, root.winfo_screenheight() - 110))
        root.geometry(f"1140x{height}+20+10")
        root.minsize(980, 640)
        root.configure(bg=BG)
        self.expression = tk.StringVar(value="x^2")
        self.a = tk.StringVar(value="0")
        self.b = tk.StringVar(value="3")
        self.precision = tk.StringVar(value="Alta · 1e-8")
        self.example = tk.StringVar(value=EXAMPLES[0].title)
        self.status = tk.StringVar(value="Escribe una función o carga un ejemplo para comenzar.")
        self.answer = tk.StringVar(value="—")
        self.integral_text = tk.StringVar(value="Integral: —")
        self.error_text = tk.StringVar(value="Error estimado: —")
        self.metrics = tk.StringVar(value="Promedio = integral / (b − a)")
        self.theme_name = "light"
        self.colors = THEMES[self.theme_name]
        self.keyboard = MathKeyboard(root, self.colors)
        self._style()
        self._build()
        self.apply_theme()
        for var in (self.expression, self.a, self.b, self.precision):
            var.trace_add("write", self._invalidate)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._poll_id = root.after(40, self._poll)

    def _style(self):
        c = self.colors
        style = ttk.Style(self.root)
        if style.theme_use() != "clam":
            style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), foreground=c["ink"], background=c["bg"],
                        bordercolor=c["axis"], lightcolor=c["axis"], darkcolor=c["axis"],
                        focuscolor=c["accent"])
        for name in ("TFrame", "TLabel", "TNotebook"):
            style.configure(name, background=c["bg"])
        for name in ("Card.TFrame", "Card.TLabel", "Muted.TLabel"):
            style.configure(name, background=c["card"])
        style.configure("Muted.TLabel", foreground=c["muted"])
        style.configure("Secondary.TLabel", foreground=c["muted"], background=c["bg"])
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 21), background=c["bg"])
        style.configure("Answer.TLabel", font=("Segoe UI Semibold", 30), foreground=c["accent"], background=c["card"])
        style.configure("TButton", padding=(10, 5), background=c["button"], foreground=c["ink"], bordercolor=c["axis"])
        style.map("TButton", background=[("active", c["hover"])], foreground=[("disabled", c["disabled"])])
        style.configure("Primary.TButton", background=c["primary"], foreground="white")
        style.map("Primary.TButton", background=[("active", c["selected"]), ("disabled", c["button"])])
        for name in ("TEntry", "TCombobox"):
            style.configure(name, padding=7, fieldbackground=c["input"], background=c["button"],
                            foreground=c["ink"], insertcolor=c["ink"], bordercolor=c["axis"],
                            selectbackground=c["selected"], selectforeground="white", arrowcolor=c["ink"])
            style.map(name, fieldbackground=[("readonly", c["input"]), ("disabled", c["bg"])],
                      foreground=[("disabled", c["disabled"]), ("readonly", c["ink"])],
                      selectbackground=[("!focus", c["input"])], selectforeground=[("!focus", c["ink"])])
        style.configure("Treeview", rowheight=29, background=c["card"], fieldbackground=c["card"], foreground=c["ink"])
        style.map("Treeview", background=[("selected", c["selected"])], foreground=[("selected", "white")])
        style.configure("Treeview.Heading", background=c["button"], foreground=c["ink"])
        style.configure("TNotebook.Tab", background=c["button"], foreground=c["muted"], padding=(6, 4))
        style.map("TNotebook.Tab", background=[("selected", c["card"]), ("active", c["hover"])],
                  foreground=[("selected", c["ink"])])
        style.configure("TCheckbutton", background=c["card"], foreground=c["ink"])
        style.map("TCheckbutton", background=[("active", c["card"])], indicatorbackground=[("selected", c["accent"]), ("!selected", c["input"])])
        for orient in ("Horizontal", "Vertical"):
            style.configure(orient + ".TScrollbar", background=c["button"], troughcolor=c["card"], arrowcolor=c["ink"])
            style.configure(orient + ".TScale", background=c["button"], troughcolor=c["input"])
        style.configure("Horizontal.TProgressbar", background=c["accent"], troughcolor=c["input"])
        self.root.option_add("*TCombobox*Listbox.background", c["input"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["ink"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["selected"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "white")

    def apply_theme(self):
        self.colors = THEMES[self.theme_name]
        self.root.configure(bg=self.colors["bg"])
        self._style()
        def recolor(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, tk.Text):
                    widget.configure(bg=self.colors["card"], fg=self.colors["ink"],
                                     insertbackground=self.colors["ink"], selectbackground=self.colors["selected"])
                recolor(widget)
        recolor(self.root)
        self.graph.set_theme(self.colors)
        self.keyboard.set_theme(self.colors)
        self.theme_button.configure(text="☀ Modo claro" if self.theme_name == "dark" else "☾ Modo oscuro")

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()

    def _build(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)
        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Cálculo del promedio de una función matemática", style="Title.TLabel").pack(side="left")
        self.theme_button = ttk.Button(header, text="☾ Modo oscuro", command=self.toggle_theme)
        self.theme_button.pack(side="right", padx=(10, 0))
        ttk.Label(outer, text="Explora una función. Integra. Comprende su valor promedio.",
                  style="Secondary.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 12))
        body = ttk.Frame(outer)
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body, style="Card.TFrame", padding=14, width=325)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.grid_propagate(False)
        left.columnconfigure(0, weight=1)
        row = 0
        def label(text):
            nonlocal row
            ttk.Label(left, text=text, style="Card.TLabel").grid(
                row=row, column=0, sticky="w", pady=(8 if row else 0, 4))
            row += 1
        label("FUNCIÓN")
        formula_row = ttk.Frame(left, style="Card.TFrame")
        formula_row.grid(row=row, column=0, sticky="ew")
        formula_row.columnconfigure(0, weight=1)
        self.function_entry = ttk.Entry(formula_row, textvariable=self.expression, font=("Consolas", 13), width=16)
        self.function_entry.grid(row=0, column=0, sticky="ew")
        self.keyboard_button = ttk.Button(formula_row, text="⌨", width=3,
                                          command=self.toggle_keyboard, takefocus=False)
        self.keyboard_button.grid(row=0, column=1, padx=(5, 0))
        row += 1
        ttk.Label(left, text="Ejemplo: cos(pi*x), sqrt(x), x^2\nUsa * para multiplicar y punto decimal.",
                  style="Muted.TLabel", wraplength=280).grid(row=row, column=0, sticky="w", pady=(6, 0))
        row += 1
        label("INTERVALO  [a, b]")
        bounds = ttk.Frame(left, style="Card.TFrame")
        bounds.grid(row=row, column=0, sticky="ew")
        bounds.columnconfigure((0, 1), weight=1)
        self.a_entry = ttk.Entry(bounds, textvariable=self.a, width=10)
        self.b_entry = ttk.Entry(bounds, textvariable=self.b, width=10)
        self.a_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.b_entry.grid(row=0, column=1, sticky="ew")
        row += 1
        label("PRECISIÓN DEL PROMEDIO")
        self.precision_box = ttk.Combobox(left, textvariable=self.precision,
                                          values=list(PRECISIONS), state="readonly", width=25)
        self.precision_box.grid(row=row, column=0, sticky="ew")
        row += 1
        calculation_actions = ttk.Frame(left, style="Card.TFrame")
        calculation_actions.grid(row=row, column=0, sticky="ew", pady=(12, 3))
        calculation_actions.columnconfigure(0, weight=1)
        self.calculate_button = ttk.Button(calculation_actions, text="Calcular promedio", style="Primary.TButton",
                                           command=self.start)
        self.calculate_button.grid(row=0, column=0, sticky="ew")
        self.cancel_button = ttk.Button(calculation_actions, text="Cancelar", command=self.cancel, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=(6, 0))
        row += 1
        self.progress = ttk.Progressbar(left, mode="indeterminate")
        self.progress.grid(row=row, column=0, sticky="ew", pady=(4, 0))
        self.progress.grid_remove()
        row += 1
        label("EJEMPLOS PARA ESTUDIAR")
        self.example_box = ttk.Combobox(left, textvariable=self.example, state="readonly",
                                        values=[example.title for example in EXAMPLES], width=25)
        self.example_box.grid(row=row, column=0, sticky="ew")
        row += 1
        self.load_button = ttk.Button(left, text="Cargar ejemplo", command=self.load_example)
        self.load_button.grid(row=row, column=0, sticky="ew", pady=(7, 0))
        row += 1
        self.example_label = ttk.Label(left, text=EXAMPLES[0].explanation, wraplength=280,
                                       style="Muted.TLabel", justify="left")
        self.example_label.grid(row=row, column=0, sticky="nw", pady=(7, 0))
        row += 1
        ttk.Label(left, text="Ángulos en radianes · a < b\nFunciones reales e integrables.",
                  style="Muted.TLabel", wraplength=280).grid(row=row, column=0, sticky="sw", pady=(8, 0))
        left.rowconfigure(row, weight=1)
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        result_card = ttk.Frame(right, style="Card.TFrame", padding=(18, 8))
        result_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(result_card, text="VALOR PROMEDIO", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(result_card, textvariable=self.answer, style="Answer.TLabel").pack(anchor="w")
        ttk.Label(result_card, textvariable=self.integral_text, style="Card.TLabel").pack(anchor="w")
        ttk.Label(result_card, textvariable=self.error_text, style="Muted.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Label(result_card, textvariable=self.metrics, style="Muted.TLabel", wraplength=650).pack(anchor="w")
        self.tabs = ttk.Notebook(right)
        self.tabs.grid(row=1, column=0, sticky="nsew")
        plot_frame = ttk.Frame(self.tabs, style="Card.TFrame")
        self.tabs.add(plot_frame, text="  Gráfica  ")
        self.graph = GraphView(plot_frame, self.colors)
        self.graph.pack(fill="both", expand=True)
        self.canvas = self.graph.canvas
        self.steps = tk.Text(self.tabs, wrap="word", bg="white", fg=INK, relief="flat",
                             padx=18, pady=15, font=("Segoe UI", 11), state="disabled", width=30)
        self.tabs.add(self.steps, text="  Procedimiento  ")
        syntax = tk.Text(self.tabs, wrap="word", bg="white", fg=INK, relief="flat",
                         padx=18, pady=15, font=("Segoe UI", 11), width=30)
        syntax.insert("1.0",
            "ESCRIBIR UNA FUNCIÓN\n\nUsa x como variable. La multiplicación se escribe con *: "
            "2*x, no 2x. Las potencias usan ^ o **. Escribe paréntesis en las funciones: cos(pi*x).\n\n"
            "Operaciones: +  −  *  /  ^\nConstantes: pi, PI, π, e, tau, τ\n\n"
            "Funciones de un argumento:\nsin, sen, cos, tan, asin, acos, atan,\n"
            "sqrt, exp, log, ln, log10, abs,\nsinh, cosh, tanh.\n\n"
            "log y ln representan el logaritmo natural. Los ángulos y las funciones inversas "
            "se interpretan en radianes. Usa punto decimal: 0.5.\n\n"
            "Los límites también admiten expresiones: -pi, pi/2, sqrt(2). Deben ser finitos y a < b.\n\n"
            "CONDICIONES Y ERRORES\n\nNo se admiten complejos, expresiones por tramos, listas, "
            "comparaciones, importaciones ni instrucciones Python. El exponente evaluado se limita "
            "a [-100,100]. La expresión admite 300 caracteres y tiene límites de complejidad.\n\n"
            "sqrt(x) necesita x ≥ 0; ln(x) necesita x > 0. Una división entre cero o un desbordamiento "
            "detiene el cálculo. Alcanzar el presupuesto o no resolver la precisión produce un mensaje.\n\n"
            "La precisión compara el error estimado con max(tol_abs, tol_rel*|promedio|). "
            "No se garantiza un número fijo de decimales ni se detectan todas las discontinuidades.\n\n"
            "JSON conserva el resultado y sus condiciones. CSV contiene 501 muestras para visualizar, "
            "que no son la malla adaptativa usada al integrar. El historial dura esta sesión.")
        syntax.configure(state="disabled")
        self.tabs.add(syntax, text="  Ayuda  ")
        history_frame = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(history_frame, text="  Historial  ")
        self.history_tree = ttk.Treeview(history_frame, columns=("function", "bounds", "mean"),
                                         show="headings", selectmode="browse", height=6)
        for col, title, width in (("function", "Función", 200), ("bounds", "[a, b]", 130),
                                  ("mean", "Promedio", 160)):
            self.history_tree.heading(col, text=title)
            self.history_tree.column(col, width=width, minwidth=80)
        self.history_tree.pack(fill="both", expand=True)
        self.history_tree.bind("<Double-1>", self.restore_history)
        ttk.Button(history_frame, text="Recuperar selección", command=self.restore_history).pack(anchor="w", pady=8)
        ttk.Label(history_frame, text="Hasta 30 cálculos de esta sesión. Se pueden exportar los resultados.",
                  wraplength=600).pack(anchor="w")
        actions = ttk.Frame(right)
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.json_button = ttk.Button(actions, text="Guardar resultado JSON", command=lambda: self.save("json"), state="disabled")
        self.csv_button = ttk.Button(actions, text="Guardar muestras CSV", command=lambda: self.save("csv"), state="disabled")
        self.json_button.pack(side="left", padx=(0, 8))
        self.csv_button.pack(side="left", padx=(0, 8))
        self.image_button = ttk.Button(actions, text="Guardar gráfica PNG", command=self.save_image, state="disabled")
        self.image_button.pack(side="left")
        ttk.Label(outer, textvariable=self.status, style="Secondary.TLabel", wraplength=1080,
                  justify="left").grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.inputs = (self.function_entry, self.a_entry, self.b_entry,
                       self.precision_box, self.example_box, self.load_button, self.keyboard_button)
        for entry in (self.function_entry, self.a_entry, self.b_entry):
            self.keyboard.attach(entry)
        self.root.bind("<Return>", lambda event: self.start() if not self.busy else None)
        self._set_steps("El promedio conserva el signo de la integral.\n\n"
                        "f_prom = (1 / (b − a)) · ∫[a,b] f(x) dx\n\n"
                        "Carga un ejemplo o escribe una función. La pestaña Procedimiento "
                        "mostrará cómo interpretar el resultado.")

    def _set_steps(self, text):
        self.steps.configure(state="normal")
        self.steps.delete("1.0", "end")
        self.steps.insert("1.0", text)
        self.steps.configure(state="disabled")

    def _invalidate(self, *_):
        # Quito el resultado anterior para no confundirlo con el de la fórmula recién editada.
        self.result = None
        self.answer.set("—")
        self.integral_text.set("Integral: —")
        self.error_text.set("Error estimado: —")
        self.metrics.set("Promedio = integral / (b − a)")
        self.json_button.configure(state="disabled")
        self.csv_button.configure(state="disabled")
        self.image_button.configure(state="disabled")
        self.status.set("Entradas modificadas. Calcula para obtener un resultado actualizado.")
        self._set_steps("Se modificaron los datos. Vuelve a calcular para actualizar el procedimiento.")
        self.draw()

    def load_example(self):
        if self.busy:
            return
        selected = next((e for e in EXAMPLES if e.title == self.example.get()), EXAMPLES[0])
        self.expression.set(selected.expression)
        self.a.set(selected.a)
        self.b.set(selected.b)
        self.example_label.configure(text=selected.explanation)
        self.status.set("Ejemplo cargado. Pulsa Calcular promedio y compara con la respuesta analítica.")

    def _busy(self, value):
        self.busy = value
        for widget in self.inputs:
            widget.configure(state="disabled" if value else (
                "readonly" if isinstance(widget, ttk.Combobox) else "normal"))
        self.calculate_button.configure(state="disabled" if value else "normal")
        self.cancel_button.configure(state="normal" if value else "disabled")
        if value:
            self.progress.grid()
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def start(self):
        if self.busy:
            return
        self.keyboard.hide()
        self._invalidate()
        try:
            function = Expression.parse(self.expression.get())
            a, b = parse_bound(self.a.get()), parse_bound(self.b.get())
            tolerance = PRECISIONS[self.precision.get()]
            settings = Settings(abs_tol=tolerance, rel_tol=tolerance)
        except (ExpressionError, KeyError) as exc:
            self.status.set("Revisa los datos: " + str(exc))
            return
        self.cancel_event = threading.Event()
        self._busy(True)
        self.status.set("Calculando y contrastando Simpson con Gauss-Legendre…")
        snapshot = (self.expression.get(), self.a.get(), self.b.get(), self.precision.get())
        def worker():
            try:
                result = calculate(function, a, b, settings, cancel=self.cancel_event)
                self.messages.put(("ok", result, snapshot))
            except (CalculationError, ExpressionError) as exc:
                self.messages.put(("error", str(exc), snapshot))
            except Exception:
                self.messages.put(("error", "Se produjo un error inesperado. Revisa los datos y vuelve a intentar.", snapshot))
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        if self.closed:
            return
        try:
            while True:
                kind, payload, snapshot = self.messages.get_nowait()
                self._busy(False)
                current = (self.expression.get(), self.a.get(), self.b.get(), self.precision.get())
                # Descarto respuestas anteriores si encuentro que cambiaron las entradas.
                if self.cancel_event.is_set():
                    self.status.set("Cálculo cancelado. Puedes modificar los datos e intentar de nuevo.")
                elif current != snapshot:
                    self.status.set("Se descartó un cálculo porque las entradas cambiaron.")
                elif kind == "ok":
                    self.show_result(payload)
                else:
                    self.status.set("No se obtuvo un resultado válido: " + payload)
        except queue.Empty:
            pass
        self._poll_id = self.root.after(40, self._poll)

    def cancel(self):
        self.cancel_event.set()
        self.status.set("Cancelando…")

    def show_result(self, result: Result, *, remember=True):
        self.result = result
        self.answer.set(number(result.average))
        self.integral_text.set("Integral con signo: " + number(result.integral))
        self.error_text.set("Error estimado del promedio: " + format(result.estimated_error, ".3g"))
        self.metrics.set(f"{result.evaluations:,} evaluaciones · {result.elapsed_seconds:.3f} s · "
                         f"Tolerancias abs./rel.: {result.abs_tol:g} / {result.rel_tol:g}")
        self.json_button.configure(state="normal")
        self.csv_button.configure(state="normal")
        self.image_button.configure(state="normal")
        self.status.set("Cálculo completado. El error es una estimación numérica; revisa el dominio de la función.")
        self._set_steps(
            f"1. DATOS\nf(x) = {result.expression}\na = {number(result.a)}; b = {number(result.b)}\n"
            f"Longitud del intervalo: b − a = {number(result.b - result.a)}\n\n"
            "2. MÉTODO\nSe transforma x = a + (b−a)t, con 0 ≤ t ≤ 1. Así, el promedio "
            "es la integral de f(a+(b−a)t) en [0,1].\n\n"
            "Se aplica Simpson 1/3 y se subdividen los tramos que necesitan más precisión. "
            "La diferencia entre una estimación y su refinamiento se divide entre 15 para estimar "
            "el error en tramos suficientemente suaves. Después se contrasta con Gauss-Legendre "
            "de ocho puntos sobre otra partición.\n\n"
            f"3. RESULTADO\nI ≈ {number(result.integral)}\nf_prom = I / (b−a) ≈ {number(result.average)}\n"
            f"Error estimado del promedio: {result.estimated_error:.4g}\n\n"
            "4. INTERPRETACIÓN\nEl rectángulo de altura f_prom y base b−a tiene la misma integral "
            "con signo que la función. El promedio tiene las unidades de f(x); la integral tiene "
            "unidades de f(x) multiplicadas por las de x. Las entradas no fijan unidades físicas.\n\n"
            "5. CONDICIONES\nSe usan números reales de punto flotante. La función debe estar definida "
            "en [a,b] y ser integrable. No se resuelven integrales impropias automáticamente. "
            "Ningún muestreo finito puede detectar todas las singularidades o picos estrechos. "
            "Un resultado pequeño no equivale a un error relativo pequeño cuando el promedio es casi cero.")
        if remember:
            self.history.insert(0, result)
            del self.history[30:]
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            for i, entry in enumerate(self.history):
                self.history_tree.insert("", "end", iid=str(i), values=(
                    entry.expression, f"[{number(entry.a)}, {number(entry.b)}]", number(entry.average)))
        self.draw()

    def restore_history(self, event=None):
        if self.busy:
            return
        selected = self.history_tree.selection()
        if not selected:
            return
        result = self.history[int(selected[0])]
        self.expression.set(result.expression)
        self.a.set(repr(result.a))
        self.b.set(repr(result.b))
        for label, tolerance in PRECISIONS.items():
            if tolerance == result.abs_tol:
                self.precision.set(label)
        self.example_label.configure(text="Cálculo recuperado del historial de esta sesión.")
        self.show_result(result, remember=False)
        self.tabs.select(0)

    def draw(self):
        self.graph.set_result(self.result)

    def toggle_keyboard(self):
        if self.keyboard.visible:
            self.keyboard.hide()
        elif not self.busy:
            self.keyboard.show(self.function_entry)

    def save_image(self):
        if self.result is None or self.busy:
            return
        self.keyboard.hide()
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".png",
            initialfile="grafica-promedio.png", filetypes=[("Imagen PNG", "*.png")])
        if not path:
            return
        try:
            self.graph.save_png(path)
            self.status.set("Gráfica guardada con el tema y la vista actuales: " + path)
        except (OSError, ValueError, ImportError) as exc:
            self.status.set("No se pudo guardar la imagen: " + str(exc))

    def save(self, kind):
        if self.result is None or self.busy:
            return
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension="." + kind,
            initialfile="valor-promedio." + kind, filetypes=[(kind.upper(), "*." + kind)])
        if not path:
            return
        try:
            (export_json if kind == "json" else export_csv)(path, self.result)
            self.status.set("Archivo guardado: " + path)
        except (OSError, ValueError) as exc:
            self.status.set("No se pudo guardar el archivo: " + str(exc))

    def close(self):
        self.closed = True
        self.root.update_idletasks()
        self.keyboard.close()
        self.cancel_event.set()
        self.root.after_cancel(self._poll_id)
        self.root.destroy()

def run():
    root = tk.Tk()
    AverageApp(root)
    root.mainloop()

def smoke_test() -> dict:
    """Acá compruebo los controles, el cálculo y la gráfica, también dentro del EXE."""
    root = tk.Tk()
    root.withdraw()
    app = AverageApp(root)
    try:
        result = calculate(Expression.parse("x^2"), 0, 3)
        app.show_result(result)
        root.update_idletasks()
        app.draw()
        assert app.canvas.find_withtag("average")
        assert app.canvas.find_withtag("curve")
        assert abs(result.average - 3) < 1e-8
        app.toggle_theme()
        app.graph.zoom(0.8)
        app.keyboard.show(app.function_entry)
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            image_path = Path(temp) / "grafica.png"
            app.graph.save_png(image_path)
            assert image_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        return {"ok": True, "interface": "Tk", "average": result.average,
                "graph_items": len(app.canvas.find_all()), "theme": app.theme_name,
                "png_export": True, "keyboard_buttons": len(app.keyboard.buttons)}
    finally:
        app.close()
