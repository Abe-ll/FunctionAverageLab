"""Acá traduzco botones matemáticos a la sintaxis que ya entiende el motor."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

class MathKeyboard:
    def __init__(self, root: tk.Tk, colors: dict):
        self.root = root
        self.colors = colors
        self.target: ttk.Entry | None = None
        self.window: tk.Toplevel | None = None
        self.buttons: dict[str, ttk.Button] = {}

    @property
    def visible(self):
        return self.window is not None and self.window.winfo_viewable()

    def attach(self, entry: ttk.Entry):
        entry.bind("<FocusIn>", lambda event: self.show(entry), add="+")
        entry.bind("<ButtonRelease-1>", lambda event: self.show(entry), add="+")
        entry.bind("<Escape>", lambda event: self.hide(), add="+")

    def show(self, entry: ttk.Entry):
        if str(entry["state"]) == "disabled":
            return
        self.target = entry
        if self.window is None:
            win = self.window = tk.Toplevel(self.root)
            win.withdraw()
            win.overrideredirect(True)
            win.transient(self.root)
            win.configure(bg=self.colors["axis"], padx=1, pady=1)
            frame = ttk.Frame(win, style="Card.TFrame", padding=10)
            frame.pack(fill="both", expand=True)
            header = ttk.Frame(frame, style="Card.TFrame")
            header.pack(fill="x", pady=(0, 6))
            ttk.Label(header, text="TECLADO MATEMÁTICO", style="Muted.TLabel").pack(side="left")
            ttk.Button(header, text="Listo  ✓", command=self.hide, takefocus=False).pack(side="right")
            tabs = ttk.Notebook(frame)
            tabs.pack(fill="both", expand=True)
            rows = (
                ("Básico", (("x", "π", "e", "(", ")", "⌫"),
                            ("7", "8", "9", "÷", "√", "x²"),
                            ("4", "5", "6", "×", "xʸ", "a⁄b"),
                            ("1", "2", "3", "−", "|x|", "eˣ"),
                            ("0", ".", "+", "←", "→", "AC"))),
                ("Funciones", (("sen", "cos", "tan", "ln", "log₁₀", "√"),
                               ("asin", "acos", "atan", "sinh", "cosh", "tanh"))),
            )
            for title, keys in rows:
                panel = ttk.Frame(tabs, style="Card.TFrame", padding=4)
                tabs.add(panel, text=title)
                for r, row in enumerate(keys):
                    for c, key in enumerate(row):
                        button = ttk.Button(panel, text=key, width=7, takefocus=False,
                                            command=lambda value=key: self.press(value))
                        button.grid(row=r, column=c, sticky="ew", padx=2, pady=2)
                        self.buttons[key] = button
                for c in range(6):
                    panel.columnconfigure(c, weight=1)
            ttk.Label(frame, text="Insertá en el cursor o seleccioná algo para envolverlo.",
                      style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
            win.bind("<Escape>", lambda event: self.hide())
        self.window.update_idletasks()
        # Lo despliego sobre la zona derecha para dejar libres los datos de entrada.
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        x = min(self.root.winfo_rootx() + 345, self.root.winfo_screenwidth() - width - 12)
        y = min(entry.winfo_rooty() + entry.winfo_height() + 6,
                self.root.winfo_screenheight() - height - 65)
        self.window.geometry(f"+{max(4, x)}+{max(4, y)}")
        self.window.deiconify()
        self.window.lift()

    def hide(self):
        if self.window is not None:
            self.window.withdraw()

    def set_theme(self, colors):
        self.colors = colors
        if self.window is not None:
            self.window.configure(bg=colors["axis"])

    def press(self, key: str):
        entry = self.target
        if entry is None or str(entry["state"]) == "disabled":
            return
        try:
            start, end = entry.index("sel.first"), entry.index("sel.last")
        except tk.TclError:
            start = end = entry.index(tk.INSERT)
        text = entry.get()
        selected = text[start:end]
        before = text[:start]
        if key in ("←", "→"):
            entry.selection_clear()
            entry.icursor(max(0, min(len(text), start + (-1 if key == "←" else 1))))
            return
        if key == "⌫":
            if start == end:
                start = max(0, start - 1)
            entry.delete(start, end)
            entry.icursor(start)
            return
        if key == "AC":
            entry.delete(0, "end")
            return
        operand = bool(before and (before[-1].isalnum() or before[-1] in ")π"))
        functions = {"√": "sqrt", "|x|": "abs", "eˣ": "exp", "log₁₀": "log10",
                     **{name: name for name in ("sen", "cos", "tan", "ln", "asin",
                                                "acos", "atan", "sinh", "cosh", "tanh")}}
        offset = None
        if key in functions:
            prefix = ("*" if operand else "") + functions[key] + "("
            insert = prefix + selected + ")"
            offset = len(prefix) + len(selected)
        elif key == "x²":
            insert = f"({selected})^2" if selected else ("^2" if operand else "x^2")
        elif key == "xʸ":
            prefix = f"({selected})^(" if selected else ("^(" if operand else "x^(")
            insert, offset = prefix + ")", len(prefix)
        elif key == "a⁄b":
            if selected:
                insert, offset = f"({selected})/()", len(selected) + 4
            else:
                prefix = "*" if operand else ""
                insert, offset = prefix + "()/()", len(prefix) + 1
        else:
            insert = {"π": "pi", "÷": "/", "×": "*", "−": "-"}.get(key, key)
            if not selected and operand and (key in ("x", "π", "e", "(") or
                                             (key.isdigit() and not before[-1].isdigit()
                                              and before[-1] != ".")):
                insert = "*" + insert
        entry.delete(start, end)
        entry.insert(start, insert)
        entry.selection_clear()
        entry.icursor(start + (len(insert) if offset is None else offset))
        entry.xview(entry.index(tk.INSERT))

    def close(self):
        if self.window is not None:
            self.window.destroy()
            self.window = None
