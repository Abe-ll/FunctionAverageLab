"""Acá guardo ejemplos que puedo comparar con un resultado calculado a mano."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Example:
    title: str
    expression: str
    a: str
    b: str
    explanation: str

EXAMPLES = (
    Example("Parábola • x²", "x^2", "0", "3",
            "∫₀³ x² dx = [x³/3]₀³ = 9; promedio = 9/3 = 3."),
    Example("Seno • un arco", "sin(x)", "0", "pi",
            "∫₀^π sen(x) dx = [-cos(x)]₀^π = 2; promedio = 2/π ≈ 0.636619772368."),
    Example("Constante • altura 5", "5", "-2", "4",
            "La integral es 5·6 = 30. El promedio de una constante es la misma constante: 5."),
    Example("Simetría • x³", "x^3", "-2", "2",
            "x³ es impar. En [-2,2] las contribuciones se cancelan: integral = promedio = 0."),
    Example("Exponencial", "exp(x)", "0", "1",
            "∫₀¹ eˣ dx = e−1. El intervalo mide 1: promedio = e−1 ≈ 1.71828182846."),
    Example("Valor absoluto", "abs(x)", "-1", "1",
            "Dos triángulos de área 1/2 suman 1; promedio = 1/2."),
    Example("Raíz cuadrada", "sqrt(x)", "0", "1",
            "∫₀¹ √x dx = [2x^(3/2)/3]₀¹ = 2/3; promedio = 2/3."),
    Example("Oscilación • prueba de malla", "cos(800*pi*x)", "0", "1",
            "La antiderivada es sen(800πx)/(800π). En [0,1] el promedio es 0. "
            "Una malla uniforme mal elegida puede evaluar siempre cerca de 1."),
)
