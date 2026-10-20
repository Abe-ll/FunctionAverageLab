"""Acá comparto el trazado entre la ventana y la imagen, sin capturar el escritorio."""
from __future__ import annotations
import math
import re
from functools import lru_cache
import os
import tkinter as tk
from dataclasses import dataclass, replace
from pathlib import Path
from tkinter import ttk

from .expressions import Expression, ExpressionError
from .numerics import Result
from .themes import THEMES

@dataclass(frozen=True)
class Viewport:
    # Uso x normalizada e y escalada para no desbordar al dibujar valores enormes.
    left: float
    right: float
    bottom: float
    top: float
    scale: float

    def zoom(self, factor: float, x=0.5, y=0.5):
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("El factor de zoom debe ser positivo y finito.")
        span = self.right - self.left
        height = self.top - self.bottom
        if not (1e-10 <= span * factor <= 1e5 and 1e-10 <= height * factor <= 1e5):
            return self
        cx, cy = self.left + span * x, self.bottom + height * y
        result = replace(self, left=cx - span * factor * x, right=cx + span * factor * (1 - x),
                         bottom=cy - height * factor * y, top=cy + height * factor * (1 - y))
        return result if result.left < result.right and result.bottom < result.top else self

    def pan(self, dx: float, dy: float):
        if not all(math.isfinite(n) and abs(n) < 1e8 for n in (dx, dy)):
            return self
        result = replace(self, left=self.left + dx, right=self.right + dx,
                         bottom=self.bottom + dy, top=self.top + dy)
        return result if result.left < result.right and result.bottom < result.top else self

@dataclass(frozen=True)
class Preview:
    expression: str
    a: float
    b: float
    average: float | None = None

@lru_cache(maxsize=32)
def parsed_function(source):
    return Expression.parse(source)

def curve_samples(result: Result | Preview, left=0.0, right=1.0, count=801):
    function = parsed_function(result.expression)
    left, right = max(0.0, left), min(1.0, right)
    if left > right:
        return []
    samples = []
    for i in range(count):
        t = left + (right - left) * i / (count - 1)
        x = result.a if t == 0 else result.b if t == 1 else result.a + (result.b - result.a) * t
        try:
            y = function(x)
        except ExpressionError:
            y = None
        samples.append((t, y))
    return samples

def fit_view(result: Result | Preview, comparisons=()):
    values = [y for _, y in curve_samples(result) if y is not None] + [0.0]
    if result.average is not None:
        values.append(result.average)
    for source, _ in comparisons:
        values.extend(y for _, y in curve_samples(Preview(source, result.a, result.b)) if y is not None)
    scale = max(map(abs, values)) or 1.0
    lo, hi = min(y / scale for y in values), max(y / scale for y in values)
    margin = max((hi - lo) * 0.09, 0.08)
    return Viewport(-0.04, 1.04, lo - margin, hi + margin, scale)

def ticks(lo: float, hi: float, count=6):
    raw = (hi - lo) / count
    unit = 10 ** math.floor(math.log10(raw))
    step = next(n * unit for n in (1, 2, 5, 10) if n * unit >= raw)
    first = math.ceil(lo / step)
    return [(first + i) * step for i in range(20)
            if lo <= (first + i) * step <= hi]

def label(value: float):
    if not math.isfinite(value):
        return "fuera de rango"
    return format(0.0 if value == 0 else value, ".6g")

def display_formula(source):
    # Cambio solo la presentación; el motor conserva la expresión original.
    text=source.replace("**","^")
    text=re.sub(r"\^([23])(?![\w.])",lambda m:{"2":"²","3":"³"}[m[1]],text)
    text=re.sub(r"\bpi\b","π",text)
    return text.replace("sqrt(","√(").replace("sin(","sen(").replace("*","·")

def axis_label(value: float, spacing: float):
    if not math.isfinite(value) or not math.isfinite(spacing) or spacing <= 0:
        return label(value)
    # Aumento los dígitos al acercarme para que dos marcas no parezcan el mismo número.
    digits = min(17, max(4, math.ceil(math.log10(max(abs(value), spacing)))
                        - math.floor(math.log10(spacing)) + 1))
    return format(0.0 if value == 0 else value, f".{digits}g")

def clip_line(x1, y1, x2, y2, width, height):
    # Recorto cada segmento: una curva fuera de vista no debe pintar sobre los rótulos.
    dx, dy = x2 - x1, y2 - y1
    if not all(math.isfinite(n) for n in (dx, dy)):
        return None
    low, high = 0.0, 1.0
    for p, q in ((-dx, x1), (dx, width - x1), (-dy, y1), (dy, height - y1)):
        if p == 0:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                low = max(low, r)
            else:
                high = min(high, r)
            if low > high:
                return None
    return x1 + low * dx, y1 + low * dy, x1 + high * dx, y1 + high * dy

def scene(result: Result, view: Viewport, width: int, height: int, colors: dict,
          grid=True, axes=True, samples=None, extras=()):
    pad_left, pad_right, pad_top, pad_bottom = 82, 24, 26 + len(extras)*18, 44
    w, h = max(30, width - pad_left - pad_right), max(30, height - pad_top - pad_bottom)
    xspan, yspan = view.right - view.left, view.top - view.bottom
    items = []
    def line(coords, color, thickness=1, tag="", dash=False):
        items.append(("line", coords, color, thickness, tag, dash))
    def text(x, y, value, anchor="center", color=None):
        items.append(("text", (x, y), color or colors["muted"], value, anchor))
    def px(t):
        return (t - view.left) / xspan * w
    def py(y):
        return (view.top - y) / yspan * h
    if samples is None:
        samples = curve_samples(result, view.left, view.right, min(1601, max(501, width)))
    def paths(points):
        paths, current = [], []
        previous = None
        for t, value in points:
            if value is None:
                if current:
                    paths.append(current)
                current, previous = [], None
                continue
            point = (px(t), py(value / view.scale))
            if previous is not None:
                clipped = clip_line(*previous, *point, w, h)
                if clipped:
                    first = (clipped[0]+pad_left, clipped[1]+pad_top)
                    last = (clipped[2]+pad_left, clipped[3]+pad_top)
                    if current and (abs(current[-2]-first[0])>1e-5 or abs(current[-1]-first[1])>1e-5):
                        paths.append(current)
                        current = []
                    if not current:
                        current.extend(first)
                    current.extend(last)
                elif current:
                    paths.append(current)
                    current = []
            previous = point
        if current:
            paths.append(current)
        return paths
    zero = max(0, min(h, py(0))) + pad_top
    run, sign = [], None
    def finish_fill():
        if len(run)>=4:
            items.append(("polygon", (run[0], zero, *run, run[-2], zero),
                          colors["positive"] if sign else colors["negative"]))
    for t, value in samples:
        if value is None:
            finish_fill()
            run, sign = [], None
            continue
        new_sign = value >= 0
        if sign is not None and sign != new_sign:
            finish_fill()
            run = []
        sign = new_sign
        run.extend((pad_left + max(0,min(w,px(t))), pad_top + max(0,min(h,py(value/view.scale)))))
    finish_fill()
    # Las marcas se expresan en las unidades originales, aunque el trazado esté normalizado.
    xticks = ticks(view.left, view.right, 4)
    yticks = ticks(view.bottom, view.top, 5)
    xspace = (xticks[1]-xticks[0]) * (result.b-result.a) if len(xticks)>1 else xspan*(result.b-result.a)
    yspace = (yticks[1]-yticks[0]) * view.scale if len(yticks)>1 else yspan*view.scale
    for t in xticks:
        x = pad_left + px(t)
        if grid:
            line((x, pad_top, x, pad_top + h), colors["grid"], tag="grid")
        text(x, pad_top + h + 18, axis_label(result.a + (result.b - result.a) * t, xspace))
    for y in yticks:
        yy = pad_top + py(y)
        if grid:
            line((pad_left, yy, pad_left + w, yy), colors["grid"], tag="grid")
        text(pad_left - 9, yy, axis_label(y * view.scale, yspace), "e")
    if axes:
        if view.bottom <= 0 <= view.top:
            line((pad_left, pad_top + py(0), pad_left + w, pad_top + py(0)),
                 colors["axis"], tag="axis")
        tzero = -result.a / (result.b - result.a)
        if view.left <= tzero <= view.right:
            x = pad_left + px(tzero)
            line((x, pad_top, x, pad_top + h), colors["axis"], tag="axis")
    for source, color, points in extras:
        for coords in paths(points):
            line(coords, color, 2, "comparison")
    for coords in paths(samples):
        line(coords, colors["curve"], 2, "curve")
    mean = result.average / view.scale if result.average is not None else None
    if mean is not None and view.bottom <= mean <= view.top:
        yy = pad_top + py(mean)
        line((pad_left, yy, pad_left + w, yy), colors["mean"], 2, "average", True)
        text(pad_left + w - 5, max(pad_top + 10, yy - 12),
             "promedio = " + label(result.average), "e", colors["mean"])
    elif mean is not None:
        text(pad_left + w - 5, pad_top + 5, "Promedio fuera de vista", "e", colors["mean"])
    text(pad_left + w, pad_top + h + 34, "x")
    text(pad_left + 4, 12, "f(x) = " + display_formula(result.expression)[:60], "w", colors["curve"])
    for i,(source,color,_) in enumerate(extras):
        text(pad_left+4,30+i*18,f"g{i+1}(x) = {display_formula(source)[:55]}","w",color)
    return items

def paint_canvas(canvas: tk.Canvas, items):
    for item in items:
        kind, coords, color, *rest = item
        if kind == "line":
            thickness, tag, dashed = rest
            canvas.create_line(*coords, fill=color, width=thickness,
                               tags=(tag,), dash=(7, 4) if dashed else ())
        elif kind == "polygon":
            canvas.create_polygon(*coords, fill=color, outline="")
        else:
            value, anchor = rest
            canvas.create_text(*coords, text=value, anchor=anchor, fill=color, font=("Segoe UI", 9))

def image_font(size: int):
    from PIL import ImageFont
    for path in (Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf",
                 Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                 Path("/System/Library/Fonts/Supplemental/Arial.ttf")):
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)

def export_png(path: str | Path, result: Result, view: Viewport, colors: dict,
               grid=True, axes=True, comparisons=()):
    from PIL import Image, ImageDraw
    width, graph_height, header = 1600, 850, 150
    image = Image.new("RGB", (width, graph_height + header), colors["card"])
    painter = ImageDraw.Draw(image)
    painter.text((40, 25), "Cálculo del promedio de una función matemática",
                 font=image_font(28), fill=colors["ink"])
    formula = result.expression if len(result.expression) < 100 else result.expression[:97] + "…"
    painter.text((40, 68), "f(x) = " + formula, font=image_font(21), fill=colors["curve"])
    painter.text((40, 103), f"Intervalo [{label(result.a)}, {label(result.b)}]    "
                 f"Promedio ≈ {label(result.average)}    Error estimado: {result.estimated_error:.3g}",
                 font=image_font(20), fill=colors["muted"])
    extras = [(source, color, curve_samples(Preview(source, result.a, result.b), view.left, view.right, 1601))
              for source, color in comparisons]
    for item in scene(result, view, width, graph_height, colors, grid, axes, extras=extras):
        kind, coords, color, *rest = item
        coords = tuple(v + (header if i % 2 else 0) for i, v in enumerate(coords))
        if kind == "polygon":
            painter.polygon(coords, fill=color)
        elif kind == "line":
            thickness, _, dashed = rest
            if dashed:
                x1, y1, x2, y2 = coords
                for start in range(int(x1), int(x2), 16):
                    painter.line((start, y1, min(start + 10, x2), y2), fill=color, width=3)
            else:
                painter.line(coords, fill=color, width=max(1, thickness))
        else:
            value, anchor = rest
            painter.text(coords, value, fill=color, font=image_font(16),
                         anchor={"center": "mm", "e": "rm", "w": "lm"}[anchor])
    image.save(path, format="PNG")

class GraphView(ttk.Frame):
    def __init__(self, master, colors):
        super().__init__(master, style="Card.TFrame")
        self.colors = colors
        self.result = None
        self.view = self.home = None
        self._drag = None
        self._frame_id = None
        self._sample_cache = {}
        self.comparisons = []
        self.curve_color = None
        self.fullscreen_callback = None
        self.grid_visible = tk.BooleanVar(value=True)
        self.axes_visible = tk.BooleanVar(value=True)
        toolbar = ttk.Frame(self, style="Card.TFrame", padding=(8, 4))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew")
        for title, command in (("−", lambda: self.zoom(1.25)),
                                ("+", lambda: self.zoom(0.8)), ("Ajustar", self.fit)):
            ttk.Button(toolbar, text=title, width=7 if title == "Ajustar" else 3,
                       command=command).pack(side="left", padx=(0, 4))
        ttk.Checkbutton(toolbar, text="Cuadrícula", variable=self.grid_visible,
                        command=self.draw).pack(side="left", padx=(7, 4))
        ttk.Checkbutton(toolbar, text="Ejes", variable=self.axes_visible,
                        command=self.draw).pack(side="left")
        self.canvas = tk.Canvas(self, bg=colors["card"], highlightthickness=0,
                                height=130, width=300, cursor="fleur", takefocus=True)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.xbar = ttk.Scrollbar(self, orient="horizontal", command=lambda *a: self.scroll("x", *a))
        self.xbar.grid(row=2, column=0, sticky="ew")
        self.ybar = ttk.Scrollbar(self, orient="vertical", command=lambda *a: self.scroll("y", *a))
        self.ybar.grid(row=1, column=1, sticky="ns")
        zoom_panel = ttk.Frame(self, style="Card.TFrame", padding=(4, 0))
        zoom_panel.grid(row=1, column=2, sticky="ns")
        ttk.Label(zoom_panel, text="Zoom", style="Muted.TLabel").pack()
        self.zoom_level = tk.DoubleVar(value=0)
        self._setting_zoom = False
        self.zoom_scale = ttk.Scale(zoom_panel, orient="vertical", from_=6, to=-2,
                                    variable=self.zoom_level, command=self._slide)
        self.zoom_scale.pack(fill="y", expand=True, pady=6)
        self.fullscreen_button = ttk.Button(toolbar, text="⛶ Pantalla completa", command=self._fullscreen)
        self.fullscreen_button.pack(side="right", padx=(10,0))
        self.hint = ttk.Label(self, text="Rueda: zoom · Arrastrá para mover · Ajustar: vista inicial",
                              style="Muted.TLabel", padding=(10, 4), wraplength=620)
        self.hint.grid(row=3, column=0, columnspan=3, sticky="w")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.canvas.bind("<Configure>", lambda event: self.request_draw())
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda e: self._wheel(e, 0.8))
        self.canvas.bind("<Button-5>", lambda e: self._wheel(e, 1.25))
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Double-Button-1>", lambda e: self.fit())
        for key, dx, dy in (("Left", -.1, 0), ("Right", .1, 0),
                            ("Up", 0, .1), ("Down", 0, -.1)):
            self.canvas.bind("<" + key + ">", lambda e, x=dx, y=dy: self.pan(x, y))

    def set_result(self, result):
        if result is not self.result:
            self.result = result
            self._sample_cache.clear()
            self.home = self.view = fit_view(result, self.comparisons) if result else None
        self.draw()

    def set_theme(self, colors):
        self.colors = colors
        self.canvas.configure(bg=colors["card"])
        self.draw()

    def fit(self):
        self.view = self.home
        self.draw()

    def zoom(self, factor, x=0.5, y=0.5):
        if self.view is not None:
            self.view = self.view.zoom(factor, x, y)
            self.draw()

    def pan(self, dx, dy):
        if self.view is not None:
            self.view = self.view.pan(dx * (self.view.right - self.view.left),
                                      dy * (self.view.top - self.view.bottom))
            self.draw()

    def _slide(self, value):
        if self._setting_zoom or self.view is None:
            return
        target = (self.home.right - self.home.left) / 2 ** float(value)
        factor = target / (self.view.right - self.view.left)
        if abs(factor - 1) > 1e-8:
            self.zoom(factor)

    def _wheel(self, event, factor=None):
        if self.view is None:
            return
        extra = 18*sum(source != self.result.expression for source,_ in self.comparisons)
        width, height = self.canvas.winfo_width() - 106, self.canvas.winfo_height() - 70-extra
        x = min(1, max(0, (event.x - 82) / max(1, width)))
        y = min(1, max(0, 1 - (event.y - 26-extra) / max(1, height)))
        self.zoom(factor if factor else (0.8 if event.delta > 0 else 1.25), x, y)
        return "break"

    def _press(self, event):
        self.canvas.focus_set()
        self._drag = (event.x, event.y, self.view)

    def _motion(self, event):
        if self._drag is None or self._drag[2] is None:
            return
        x, y, old = self._drag
        dx = (x - event.x) / max(1, self.canvas.winfo_width() - 106)
        extra = 18*sum(source != self.result.expression for source,_ in self.comparisons)
        dy = (event.y - y) / max(1, self.canvas.winfo_height() - 70-extra)
        self.view = old.pan(dx * (old.right - old.left), dy * (old.top - old.bottom))
        self.request_draw()

    def _release(self, event=None):
        self._drag = None
        self.draw()

    def _extent(self):
        view, home = self.view, self.home
        w, h = home.right - home.left, home.top - home.bottom
        return (min(home.left - 3*w, view.left), max(home.right + 3*w, view.right),
                min(home.bottom - 3*h, view.bottom), max(home.top + 3*h, view.top))

    def scroll(self, axis, operation, value, units=None):
        if self.view is None:
            return
        v = self.view
        lo, hi, bottom, top = self._extent()
        if operation == "moveto":
            fraction = min(1, max(0, float(value)))
            delta = lo + fraction * (hi-lo) - v.left if axis == "x" else (
                top - fraction * (top-bottom) - v.top)
        else:
            delta = int(value) * (0.85 if units == "pages" else 0.08)
            delta *= (v.right-v.left) if axis == "x" else -(v.top-v.bottom)
        self.view = v.pan(delta if axis == "x" else 0, delta if axis == "y" else 0)
        self.draw()

    def request_draw(self):
        # Agrupo los eventos rápidos del ratón en un único fotograma pendiente.
        if self._frame_id is None:
            self._frame_id = self.after(16, self._scheduled_draw)

    def _scheduled_draw(self):
        self._frame_id = None
        self.draw()

    def _fullscreen(self):
        if self.fullscreen_callback:
            self.fullscreen_callback()

    def set_comparisons(self, curves):
        changed = [c[0] for c in curves] != [c[0] for c in self.comparisons]
        self.comparisons = list(curves)
        if changed:
            self._sample_cache.clear()
        if changed and self.result is not None:
            self.home = self.view = fit_view(self.result, self.comparisons)
        self.draw()

    def _samples(self, result):
        key = (result.expression, result.a, result.b)
        cached = self._sample_cache.get(key)
        span = self.view.right-self.view.left
        left, right = max(0,self.view.left), min(1,self.view.right)
        if cached is not None:
            lo, hi, points = cached
            covered = lo <= left and hi >= right
            detailed = (hi-lo) <= max(span*3, 1e-10)
            if self._drag is not None or (covered and detailed):
                return points
        lo, hi = max(0,left-span*.5), min(1,right+span*.5)
        points = curve_samples(result, lo, hi, 1001) if lo<=hi else []
        self._sample_cache[key] = (lo,hi,points)
        return points

    def draw(self):
        if self._frame_id is not None:
            self.after_cancel(self._frame_id)
            self._frame_id = None
        self.canvas.delete("all")
        width, height = max(200, self.canvas.winfo_width()), max(130, self.canvas.winfo_height())
        if self.result is None:
            self.canvas.create_text(width/2, height/2, text="Escribí una función para verla acá",
                                    fill=self.colors["muted"], font=("Segoe UI", 12))
            self.xbar.set(0,1)
            self.ybar.set(0,1)
            return
        colors = dict(self.colors)
        if self.curve_color:
            colors["curve"] = self.curve_color
        extras = [(source, color, self._samples(Preview(source,self.result.a,self.result.b)))
                  for source,color in self.comparisons if source != self.result.expression]
        paint_canvas(self.canvas, scene(self.result,self.view,width,height,colors,
                    self.grid_visible.get(),self.axes_visible.get(), self._samples(self.result), extras))
        lo,hi,bottom,top = self._extent()
        self.xbar.set((self.view.left-lo)/(hi-lo),(self.view.right-lo)/(hi-lo))
        self.ybar.set((top-self.view.top)/(top-bottom),(top-self.view.bottom)/(top-bottom))
        value = max(-2,min(6,math.log2((self.home.right-self.home.left)/(self.view.right-self.view.left))))
        if abs(self.zoom_level.get()-value)>1e-8:
            self._setting_zoom = True
            self.zoom_level.set(value)
            self._setting_zoom = False

    def save_png(self, path):
        if self.result is None or self.result.average is None:
            raise ValueError("Primero calculá un resultado.")
        colors = dict(self.colors)
        if self.curve_color:
            colors["curve"] = self.curve_color
        export_png(path,self.result,self.view,colors,self.grid_visible.get(),
                   self.axes_visible.get(),self.comparisons)

    def destroy(self):
        if self._frame_id is not None:
            self.after_cancel(self._frame_id)
            self._frame_id = None
        super().destroy()
