"""Intérprete matemático restringido: valida el AST completo antes de calcular."""
from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass

class ExpressionError(ValueError):
    """Error de sintaxis, dominio o rango explicado al usuario."""

OPERATIONS = {ast.Add: operator.add, ast.Sub: operator.sub,
              ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
FUNCTIONS = {name: getattr(math, name) for name in
             ("sin", "cos", "tan", "sqrt", "exp", "log", "log10",
              "asin", "acos", "atan", "sinh", "cosh", "tanh")}
FUNCTIONS.update({"abs": abs, "sen": math.sin, "ln": math.log})
CONSTANTS = {"pi": math.pi, "PI": math.pi, "π": math.pi,
             "e": math.e, "tau": math.tau, "τ": math.tau}

def finite(value: object, label: str = "El resultado") -> float:
    if type(value) not in (int, float):
        raise ExpressionError(f"{label} debe ser un número real.")
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise ExpressionError(f"{label} está fuera del rango numérico.") from exc
    if not math.isfinite(result):
        raise ExpressionError(f"{label} debe ser finito.")
    return result

@dataclass(frozen=True)
class Expression:
    source: str
    tree: ast.expr
    uses_x: bool

    @classmethod
    def parse(cls, text: str, *, allow_x: bool = True) -> "Expression":
        source = text.strip().replace("^", "**")
        if not source:
            raise ExpressionError("Escribe una expresión matemática.")
        if len(source) > 300:
            raise ExpressionError("La expresión admite hasta 300 caracteres.")
        try:
            tree = ast.parse(source, mode="eval").body
        except (SyntaxError, RecursionError, ValueError) as exc:
            raise ExpressionError("Revisa la expresión. Usa * para multiplicar y paréntesis completos.") from exc
        if sum(1 for _ in ast.walk(tree)) > 128:
            raise ExpressionError("La expresión tiene demasiadas operaciones.")
        uses_x = False

        def validate(node: ast.AST, depth: int = 0) -> None:
            nonlocal uses_x
            if depth > 24:
                raise ExpressionError("Demasiados paréntesis u operaciones anidadas.")
            if isinstance(node, ast.Constant):
                finite(node.value, "La constante")
            elif isinstance(node, ast.Name):
                if node.id == "x" and allow_x:
                    uses_x = True
                elif node.id not in CONSTANTS:
                    if node.id == "x":
                        raise ExpressionError("Los límites no pueden depender de x.")
                    raise ExpressionError(f"Nombre no admitido: {node.id}.")
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                validate(node.operand, depth + 1)
            elif isinstance(node, ast.BinOp) and type(node.op) in OPERATIONS:
                validate(node.left, depth + 1)
                validate(node.right, depth + 1)
            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                    raise ExpressionError("Usa una de las funciones matemáticas admitidas.")
                if len(node.args) != 1 or node.keywords:
                    raise ExpressionError(f"{node.func.id} necesita exactamente un argumento.")
                validate(node.args[0], depth + 1)
            else:
                raise ExpressionError("Operación no admitida. Usa números, x, +, -, *, / y potencias.")
        validate(tree)
        return cls(source, tree, uses_x)

    def __call__(self, x: float = 0.0) -> float:
        x = finite(x, "x")
        def evaluate(node: ast.expr) -> float:
            if isinstance(node, ast.Constant):
                return float(node.value)
            if isinstance(node, ast.Name):
                return x if node.id == "x" else CONSTANTS[node.id]
            if isinstance(node, ast.UnaryOp):
                value = evaluate(node.operand)
                return -value if isinstance(node.op, ast.USub) else value
            if isinstance(node, ast.BinOp):
                left, right = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Pow) and abs(right) > 100:
                    raise ExpressionError("El exponente evaluado debe estar entre -100 y 100.")
                return finite(OPERATIONS[type(node.op)](left, right))
            if isinstance(node, ast.Call):
                value = evaluate(node.args[0])
                if node.func.id == "tan" and abs(math.cos(value)) < 1e-14:
                    raise ExpressionError("La tangente no está definida en este punto.")
                return finite(FUNCTIONS[node.func.id](value))
            raise ExpressionError("Expresión no admitida.")
        try:
            return finite(evaluate(self.tree))
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            raise ExpressionError(f"En x={x:.10g}: {exc}") from exc

def parse_bound(text: str) -> float:
    return Expression.parse(text, allow_x=False)()
