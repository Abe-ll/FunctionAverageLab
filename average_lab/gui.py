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

from .themes import THEMES, CURVE_COLORS
from .plotting import GraphView, Preview, display_formula
from .keyboard import MathKeyboard
from .examples import EXAMPLES
from .expressions import Expression, ExpressionError, parse_bound
from .numerics import CalculationError, CancelledError, Result, Settings, calculate, validate_interval

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
        self.comparisons = []
        self.preview_id = None
        self.presentation_window = None
        self.presentation_graph = None
        self.presentation_entry = None
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
        self.curve_name = tk.StringVar(value="Morado")
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
        if self.presentation_graph is not None:
            self.presentation_graph.set_theme(self.colors)
        if hasattr(self, "examples_window"):
            self.examples_window.configure(bg=self.colors["card"])
        self._sync_curve_colors()
        self.keyboard.set_theme(self.colors)
        self.theme_button.configure(text="☀ Modo claro" if self.theme_name == "dark" else "☾ Modo oscuro")

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()

    def _build(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0,weight=1)
        outer.rowconfigure(2,weight=1)
        header=ttk.Frame(outer)
        header.grid(row=0,column=0,sticky="ew")
        ttk.Label(header,text="Cálculo del promedio de una función matemática",style="Title.TLabel").pack(side="left")
        self.theme_button=ttk.Button(header,text="Modo oscuro",command=self.toggle_theme)
        self.theme_button.pack(side="right")
        ttk.Label(outer,text="Escribí una función, explorá la gráfica y calculá su promedio.",
                  style="Secondary.TLabel").grid(row=1,column=0,sticky="w",pady=(2,10))
        body=ttk.Frame(outer)
        body.grid(row=2,column=0,sticky="nsew")
        body.columnconfigure(1,weight=1)
        body.rowconfigure(0,weight=1)
        left=ttk.Frame(body,style="Card.TFrame",padding=13,width=330)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        left.grid_propagate(False)
        left.columnconfigure(0,weight=1)
        formula=ttk.Frame(left,style="Card.TFrame")
        formula.grid(row=0,column=0,sticky="ew",pady=(0,10))
        formula.columnconfigure(1,weight=1)
        self.function_badge=ttk.Label(formula,text="● f(x) =",style="Card.TLabel")
        self.function_badge.grid(row=0,column=0,padx=(0,6))
        self.function_entry=ttk.Entry(formula,textvariable=self.expression,font=("Consolas",12),width=12)
        self.function_entry.grid(row=0,column=1,sticky="ew")
        self.keyboard_button=ttk.Button(formula,text="⌨",width=2,command=self.toggle_keyboard,takefocus=False)
        self.keyboard_button.grid(row=0,column=2,padx=(4,0))
        self.help_button=ttk.Button(formula,text="?",width=2,command=self.show_examples,takefocus=False)
        self.help_button.grid(row=0,column=3,padx=(3,0))
        ttk.Label(left,text="INTERVALO  [a, b]",style="Muted.TLabel").grid(row=1,column=0,sticky="w")
        bounds=ttk.Frame(left,style="Card.TFrame")
        bounds.grid(row=2,column=0,sticky="ew",pady=(5,10))
        bounds.columnconfigure((0,1),weight=1)
        self.a_entry=ttk.Entry(bounds,textvariable=self.a,width=9)
        self.b_entry=ttk.Entry(bounds,textvariable=self.b,width=9)
        self.a_entry.grid(row=0,column=0,sticky="ew",padx=(0,6))
        self.b_entry.grid(row=0,column=1,sticky="ew")
        ttk.Label(left,text="PRECISIÓN",style="Muted.TLabel").grid(row=3,column=0,sticky="w")
        self.precision_box=ttk.Combobox(left,textvariable=self.precision,values=list(PRECISIONS),state="readonly",width=24)
        self.precision_box.grid(row=4,column=0,sticky="ew",pady=(5,10))
        actions=ttk.Frame(left,style="Card.TFrame")
        actions.grid(row=5,column=0,sticky="ew")
        actions.columnconfigure(0,weight=1)
        self.calculate_button=ttk.Button(actions,text="Calcular promedio",style="Primary.TButton",command=self.start)
        self.calculate_button.grid(row=0,column=0,sticky="ew")
        self.cancel_button=ttk.Button(actions,text="Cancelar",command=self.cancel,state="disabled")
        self.cancel_button.grid(row=0,column=1,padx=(5,0))
        self.progress=ttk.Progressbar(left,mode="indeterminate")
        self.progress.grid(row=6,column=0,sticky="ew",pady=5)
        self.progress.grid_remove()
        self.result_card=ttk.Frame(left,style="Card.TFrame",padding=(0,15))
        self.result_card.grid(row=7,column=0,sticky="ew")
        ttk.Label(self.result_card,text="VALOR PROMEDIO",style="Muted.TLabel").pack(anchor="w")
        ttk.Label(self.result_card,textvariable=self.answer,style="Answer.TLabel").pack(anchor="w")
        ttk.Label(self.result_card,textvariable=self.integral_text,style="Card.TLabel",wraplength=292).pack(anchor="w")
        ttk.Label(self.result_card,textvariable=self.error_text,style="Muted.TLabel",wraplength=292).pack(anchor="w",pady=(4,0))
        ttk.Label(self.result_card,textvariable=self.metrics,style="Muted.TLabel",wraplength=292).pack(anchor="w")
        compare=ttk.Frame(left,style="Card.TFrame")
        compare.grid(row=8,column=0,sticky="ew")
        self.pin_button=ttk.Button(compare,text="+ Fijar curva",command=self.pin_curve)
        self.pin_button.pack(side="left")
        self.color_box=ttk.Combobox(compare,textvariable=self.curve_name,values=list(CURVE_COLORS),state="readonly",width=9)
        self.color_box.pack(side="right")
        self.color_box.bind("<<ComboboxSelected>>",lambda e:self._sync_curve_colors())
        self.comparison_list=ttk.Frame(left,style="Card.TFrame")
        self.comparison_list.grid(row=9,column=0,sticky="ew",pady=(5,0))
        right=ttk.Frame(body)
        right.grid(row=0,column=1,sticky="nsew")
        right.columnconfigure(0,weight=1)
        right.rowconfigure(0,weight=1)
        self.tabs=ttk.Notebook(right)
        self.tabs.grid(row=0,column=0,sticky="nsew")
        plot_frame=ttk.Frame(self.tabs,style="Card.TFrame")
        self.tabs.add(plot_frame,text=" Gráfica ")
        self.graph=GraphView(plot_frame,self.colors)
        self.graph.pack(fill="both",expand=True)
        self.graph.fullscreen_callback=self.toggle_fullscreen
        self.canvas=self.graph.canvas
        self.steps=tk.Text(self.tabs,wrap="word",relief="flat",padx=18,pady=15,font=("Segoe UI",11),state="disabled",width=30)
        self.tabs.add(self.steps,text=" Procedimiento ")
        self.syntax=tk.Text(self.tabs,wrap="word",relief="flat",padx=18,pady=15,font=("Segoe UI",11),width=30)
        self.syntax.insert("1.0","ESCRIBIR UNA FUNCIÓN\n\nUsá x como variable; también podés escribir y= o f(x)=. "
            "La multiplicación se indica con * y las potencias con ^ o **. Los ángulos están en radianes.\n\n"
            "Funciones: sin, sen, cos, tan, asin, acos, atan, sqrt, exp, ln, log, log10, abs, sinh, cosh, tanh.\n"
            "Constantes: pi, PI, π, e, tau, τ. Límites: -pi, pi/2, sqrt(2). Se requiere a<b.\n\n"
            "El botón ? abre ejemplos: al seleccionar uno se carga y calcula. El teclado ⌨ inserta plantillas.\n\n"
            "Fijar curva conserva una referencia para compararla con la siguiente función. "
            "El promedio corresponde únicamente a la función activa f(x). Hay hasta tres referencias.\n\n"
            "Pantalla completa o F11 abre la vista de presentación. Salí con Escape o con el botón Salir.\n\n"
            "No se admiten complejos, expresiones por tramos ni código Python. Se verifica dominio y finitud. "
            "La precisión compara el error estimado con max(tol_abs,tol_rel*|promedio|); no garantiza decimales. "
            "Una vista previa no demuestra integrabilidad y no tiene promedio hasta calcular.\n\n"
            "JSON conserva el resultado; CSV guarda 501 muestras de visualización. PNG guarda la vista actual.")
        self.syntax.configure(state="disabled")
        self.tabs.add(self.syntax,text=" Ayuda ")
        history=ttk.Frame(self.tabs,padding=10)
        self.tabs.add(history,text=" Historial ")
        self.history_tree=ttk.Treeview(history,columns=("function","bounds","mean"),show="headings",height=6)
        for col,title,width in (("function","Función",200),("bounds","[a,b]",130),("mean","Promedio",160)):
            self.history_tree.heading(col,text=title)
            self.history_tree.column(col,width=width,minwidth=80)
        self.history_tree.pack(fill="both",expand=True)
        self.history_tree.bind("<Double-1>",self.restore_history)
        ttk.Button(history,text="Recuperar selección",command=self.restore_history).pack(anchor="w",pady=8)
        exports=ttk.Frame(right)
        exports.grid(row=1,column=0,sticky="ew",pady=(8,0))
        self.json_button=ttk.Button(exports,text="Guardar JSON",command=lambda:self.save("json"),state="disabled")
        self.csv_button=ttk.Button(exports,text="Guardar CSV",command=lambda:self.save("csv"),state="disabled")
        self.image_button=ttk.Button(exports,text="Guardar gráfica PNG",command=self.save_image,state="disabled")
        for button in (self.json_button,self.csv_button,self.image_button):
            button.pack(side="left",padx=(0,7))
        ttk.Label(outer,textvariable=self.status,style="Secondary.TLabel",wraplength=1080).grid(row=3,column=0,sticky="ew",pady=(8,0))
        self.examples_window=tk.Toplevel(self.root)
        self.examples_window.withdraw()
        self.examples_window.title("Ejemplos y ayuda")
        self.examples_window.transient(self.root)
        self.examples_window.protocol("WM_DELETE_WINDOW",self.examples_window.withdraw)
        example_panel=ttk.Frame(self.examples_window,style="Card.TFrame",padding=18)
        example_panel.pack(fill="both",expand=True)
        ttk.Label(example_panel,text="Elegí un ejemplo",style="Card.TLabel").pack(anchor="w")
        self.example_box=ttk.Combobox(example_panel,textvariable=self.example,values=[e.title for e in EXAMPLES],state="readonly",width=40)
        self.example_box.pack(fill="x",pady=10)
        self.example_box.bind("<<ComboboxSelected>>",self._select_example)
        self.example_label=ttk.Label(example_panel,text=EXAMPLES[0].explanation,style="Muted.TLabel",wraplength=400)
        self.example_label.pack(anchor="w",pady=(0,10))
        ttk.Label(example_panel,text="Se carga y calcula al seleccionar. El teclado y la gráfica siguen disponibles.",style="Muted.TLabel",wraplength=400).pack(anchor="w")
        self.inputs=(self.function_entry,self.a_entry,self.b_entry,self.precision_box,self.keyboard_button,
                     self.help_button,self.example_box,self.pin_button)
        for entry in (self.function_entry,self.a_entry,self.b_entry):
            self.keyboard.attach(entry)
        self.root.bind("<Return>",lambda e:self.start() if not self.busy else None)
        self.root.bind("<F11>",lambda e:self.toggle_fullscreen())
        self._set_steps("El promedio conserva el signo de la integral.\n\nf_prom = ∫[a,b]f(x)dx / (b-a).")

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
        self._schedule_preview()

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
        if self.presentation_entry is not None:
            self.presentation_entry.configure(state="disabled" if value else "normal")
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
        self._cancel_preview()
        try:
            function = Expression.parse(self._function_source())
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
        self._cancel_preview()
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
        if self.presentation_graph is not None:
            self.presentation_graph.set_result(self.result)

    def _function_source(self):
        text=self.expression.get().strip()
        for prefix in ("f(x)","y"):
            if text.startswith(prefix) and text[len(prefix):].lstrip().startswith("="):
                return text.split("=",1)[1].strip()
        return text

    def _cancel_preview(self):
        if self.preview_id is not None:
            self.root.after_cancel(self.preview_id)
            self.preview_id=None

    def _schedule_preview(self):
        self._cancel_preview()
        if not self.closed:
            self.preview_id=self.root.after(220,self.preview)

    def preview(self):
        self._cancel_preview()
        if self.busy or self.result is not None:
            return
        try:
            function=Expression.parse(self._function_source())
            a,b,_=validate_interval(parse_bound(self.a.get()),parse_bound(self.b.get()))
            data=Preview(function.source,a,b)
            self.graph.set_result(data)
            if self.presentation_graph is not None:
                self.presentation_graph.set_result(data)
            self.status.set("Vista previa de f(x). Calculá para obtener el promedio y su control de error.")
        except (ExpressionError,CalculationError):
            self.status.set("Completá la función y los límites para actualizar la vista previa.")

    def show_examples(self):
        self.keyboard.hide()
        self.examples_window.deiconify()
        self.examples_window.lift()

    def _select_example(self,event=None):
        self.load_example()
        self.examples_window.withdraw()
        self.start()

    def _color(self,name):
        return CURVE_COLORS[name][self.theme_name=="dark"]

    def _sync_curve_colors(self):
        self.function_badge.configure(foreground=self._color(self.curve_name.get()))
        for graph in (self.graph,self.presentation_graph):
            if graph is not None:
                graph.curve_color=self._color(self.curve_name.get())
                graph.set_comparisons([(c["source"],self._color(c["color"])) for c in self.comparisons])
        for widget in self.comparison_list.winfo_children():
            widget.destroy()
        for i,curve in enumerate(self.comparisons):
            row=ttk.Frame(self.comparison_list,style="Card.TFrame")
            row.pack(fill="x",pady=2)
            ttk.Label(row,text=f"g{i+1}(x) = {display_formula(curve['source'])[:25]}",style="Card.TLabel",
                      foreground=self._color(curve["color"])).pack(side="left")
            ttk.Button(row,text="×",width=2,command=lambda index=i:self.remove_curve(index)).pack(side="right")

    def pin_curve(self):
        if self.busy:
            return
        try:
            source=Expression.parse(self._function_source()).source
        except ExpressionError as exc:
            self.status.set(str(exc))
            return
        if len(self.comparisons)>=3:
            self.status.set("Ya hay tres referencias. Quitá una con × para fijar otra.")
            return
        if not any(c["source"]==source for c in self.comparisons):
            self.comparisons.append({"source":source,"color":self.curve_name.get()})
            names=list(CURVE_COLORS)
            self.curve_name.set(names[(names.index(self.curve_name.get())+1)%len(names)])
            self._sync_curve_colors()
            self.status.set("Curva fijada. Escribí otra función para compararlas en la misma gráfica.")

    def remove_curve(self,index):
        del self.comparisons[index]
        self._sync_curve_colors()

    def toggle_fullscreen(self):
        if self.presentation_window is not None:
            self.leave_fullscreen()
            return
        self.keyboard.hide()
        window=self.presentation_window=tk.Toplevel(self.root)
        window.title("Gráfica - presentación")
        window.configure(bg=self.colors["bg"])
        window.attributes("-fullscreen",True)
        window.protocol("WM_DELETE_WINDOW",self.leave_fullscreen)
        bar=ttk.Frame(window,padding=10)
        bar.pack(fill="x")
        ttk.Label(bar,text="f(x) =").pack(side="left",padx=(0,8))
        entry=self.presentation_entry=ttk.Entry(bar,textvariable=self.expression,font=("Consolas",14))
        entry.configure(state="disabled" if self.busy else "normal")
        entry.pack(side="left",fill="x",expand=True)
        self.keyboard.attach(entry)
        entry.bind("<Escape>",lambda e:(
            self.keyboard.hide() if self.keyboard.visible else self.leave_fullscreen(), "break")[1])
        ttk.Button(bar,text="⌨",width=3,command=lambda:self.keyboard.show(entry)).pack(side="left",padx=5)
        ttk.Button(bar,text="?",width=3,command=self.show_examples).pack(side="left")
        ttk.Button(bar,text="Calcular",command=self.start).pack(side="left",padx=5)
        ttk.Button(bar,text="Guardar PNG",command=self.save_image).pack(side="left")
        ttk.Button(bar,text="Salir (Esc)",command=self.leave_fullscreen).pack(side="left",padx=(8,0))
        graph=self.presentation_graph=GraphView(window,self.colors)
        graph.pack(fill="both",expand=True)
        graph.fullscreen_callback=self.leave_fullscreen
        graph.fullscreen_button.configure(text="Salir de pantalla completa")
        graph.set_result(self.graph.result)
        self._sync_curve_colors()
        graph.view=self.graph.view
        graph.draw()
        window.bind("<Escape>",lambda e:self.leave_fullscreen())
        window.bind("<F11>",lambda e:self.leave_fullscreen())
        window.bind("<Return>",lambda e:self.start() if not self.busy else None)

    def leave_fullscreen(self):
        if self.presentation_window is not None:
            self.keyboard.hide()
            self.keyboard.target=self.function_entry
            if self.graph.result is self.presentation_graph.result:
                self.graph.view=self.presentation_graph.view
            self.presentation_graph=None
            self.presentation_entry=None
            window=self.presentation_window
            self.presentation_window=None
            window.destroy()
            self.graph.draw()

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
            (self.presentation_graph or self.graph).save_png(path)
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
        self._cancel_preview()
        self.leave_fullscreen()
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
