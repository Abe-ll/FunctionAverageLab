"""Consola repetible: conserva la opción de uso sin interfaz gráfica."""
from __future__ import annotations
import json
from .expressions import Expression, ExpressionError, parse_bound
from .numerics import CalculationError, calculate

def run() -> None:
    print("FUNCTION AVERAGE LAB | Valor promedio")
    print("Usa x, *, ^, sin/sen, cos, sqrt, exp, log/ln y pi. Ángulos en radianes.")
    while True:
        try:
            text = input("\nf(x), o salir: ").strip()
            if text.lower() in {"salir", "exit", "q"}:
                return
            function = Expression.parse(text)
            a = parse_bound(input("Límite inferior a: "))
            b = parse_bound(input("Límite superior b: "))
            result = calculate(function, a, b)
            print(f"Integral aproximada: {result.integral:.12g}")
            print(f"Valor promedio: {result.average:.12g}")
            print(f"Error estimado del promedio: {result.estimated_error:.3g}")
            print(result.note)
        except (ExpressionError, CalculationError) as exc:
            print(f"No se pudo calcular: {exc}\nPuedes corregir los datos o escribir salir.")
        except (EOFError, KeyboardInterrupt):
            print("\nSesión terminada.")
            return

def self_test() -> dict:
    result = calculate(Expression.parse("x^2"), 0, 3)
    if abs(result.average - 3) > 1e-8:
        raise RuntimeError("Falló la comprobación del promedio.")
    return {"ok": True, "case": "x^2 en [0,3]", "average": result.average}
