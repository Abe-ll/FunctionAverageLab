"""Simpson adaptativo con control independiente y presupuesto de trabajo.

Se conserva la idea de Simpson 1/3 del prototipo. El cálculo se normaliza
a t en [0,1]: la integral en t es directamente el promedio buscado.
La estimación de error es numérica; no demuestra continuidad ni exactitud.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import asdict, dataclass
from typing import Callable

from .expressions import Expression, ExpressionError, finite

class CalculationError(ValueError):
    pass

class CancelledError(CalculationError):
    pass

@dataclass(frozen=True)
class Settings:
    abs_tol: float = 1e-8
    rel_tol: float = 1e-8
    max_evaluations: int = 200_000
    max_depth: int = 32
    time_limit: float = 12.0

    def validate(self) -> None:
        for name in ("abs_tol", "rel_tol"):
            value = finite(getattr(self, name), "La tolerancia")
            if not 1e-12 <= value <= 1e-2:
                raise CalculationError("La tolerancia debe estar entre 1e-12 y 0.01.")
        if type(self.max_evaluations) is not int or not 100 <= self.max_evaluations <= 2_000_000:
            raise CalculationError("El presupuesto de evaluaciones no es válido.")
        if type(self.max_depth) is not int or not 4 <= self.max_depth <= 40:
            raise CalculationError("La profundidad de refinamiento no es válida.")
        if not 0.01 <= finite(self.time_limit) <= 120:
            raise CalculationError("El tiempo máximo debe estar entre 0.01 y 120 segundos.")

@dataclass(frozen=True)
class Result:
    expression: str
    a: float
    b: float
    integral: float
    average: float
    estimated_error: float
    evaluations: int
    elapsed_seconds: float
    accepted_intervals: int
    abs_tol: float
    rel_tol: float
    method: str = "Simpson 1/3 adaptativo + control Gauss-Legendre"
    note: str = "Error estimado, no cota garantizada. Se requieren funciones propias e integrables."

    def to_dict(self) -> dict:
        return asdict(self)

def validate_interval(a: float, b: float) -> tuple[float, float, float]:
    try:
        a, b = finite(a, "El límite inferior"), finite(b, "El límite superior")
        width = finite(b - a, "La longitud del intervalo")
    except ExpressionError as exc:
        raise CalculationError(str(exc)) from exc
    if width <= 0:
        raise CalculationError("El límite superior b debe ser mayor que a.")
    # No usar un paso que se redondea al extremo y aparenta convergencia.
    if not a < a + width / 2 < b or a + width / 1024 == a or b - width / 1024 == b:
        raise CalculationError("El intervalo es demasiado estrecho respecto de sus límites para float.")
    return a, b, width

# Pares positivos de la regla de Gauss-Legendre de 8 puntos en [-1,1].
GAUSS8 = ((0.1834346424956498, 0.3626837833783620),
          (0.5255324099163290, 0.3137066458778873),
          (0.7966664774136267, 0.2223810344533745),
          (0.9602898564975363, 0.1012285362903763))

def _knots(count: int, shift: float) -> list[float]:
    # La perturbación determinista evita depender de dos mallas uniformes anidadas.
    return [0.0] + [(i + 0.18 * math.sin(i * math.sqrt(2) + shift)) / count
                    for i in range(1, count)] + [1.0]

def calculate(function: Expression, a: float, b: float, settings: Settings | None = None,
              *, cancel: threading.Event | None = None) -> Result:
    settings = settings or Settings()
    settings.validate()
    a, b, width = validate_interval(a, b)
    started = time.perf_counter()
    cache: dict[float, float] = {}
    accepted = 0

    def sample(t: float) -> float:
        if cancel is not None and cancel.is_set():
            raise CancelledError("Cálculo cancelado.")
        if time.perf_counter() - started > settings.time_limit:
            raise CalculationError("Se alcanzó el tiempo máximo. Reduce el intervalo o revisa la función.")
        if t in cache:
            return cache[t]
        if len(cache) >= settings.max_evaluations:
            raise CalculationError("Se agotó el presupuesto de precisión. Revisa oscilaciones o discontinuidades.")
        x = a if t == 0 else b if t == 1 else a + width * t
        try:
            value = finite(function(x))
        except (ExpressionError, OverflowError, ZeroDivisionError) as exc:
            raise CalculationError(str(exc)) from exc
        cache[t] = value
        return value

    def panel(left: float, right: float, fl: float, fm: float, fr: float) -> float:
        # Dividir antes de sumar reduce desbordamientos intermedios evitables.
        return finite((right - left) * math.fsum((fl / 6, (2 / 3) * fm, fr / 6)))

    knots = _knots(32, 0.0)
    seeds = []
    for left, right in zip(knots, knots[1:]):
        mid = (left + right) / 2
        fl, fm, fr = sample(left), sample(mid), sample(right)
        seeds.append((left, right, fl, fm, fr, panel(left, right, fl, fm, fr)))
    initial = finite(math.fsum(s[-1] for s in seeds))
    target = max(settings.abs_tol, settings.rel_tol * abs(initial)) / 4

    def refine(left: float, right: float, fl: float, fm: float, fr: float,
               whole: float, tolerance: float, depth: int) -> tuple[float, float]:
        nonlocal accepted
        mid = (left + right) / 2
        q1, q3 = (left + mid) / 2, (mid + right) / 2
        if q1 == left or q3 == right:
            raise CalculationError("Se alcanzó la resolución de punto flotante.")
        fq1, fq3 = sample(q1), sample(q3)
        first = panel(left, mid, fl, fq1, fm)
        second = panel(mid, right, fm, fq3, fr)
        both = finite(math.fsum((first, second)))
        delta = finite(both - whole)
        error = abs(delta) / 15
        if error <= max(tolerance, settings.abs_tol * 1e-6):
            accepted += 1
            return finite(both + delta / 15), error
        if depth >= settings.max_depth:
            raise CalculationError("No se resolvió el intervalo: posible singularidad o falta de suavidad.")
        v1, e1 = refine(left, mid, fl, fq1, fm, first, tolerance / 2, depth + 1)
        v2, e2 = refine(mid, right, fm, fq3, fr, second, tolerance / 2, depth + 1)
        return finite(math.fsum((v1, v2))), e1 + e2

    def integrate(tolerance: float) -> tuple[float, float]:
        values, errors = [], []
        for left, right, fl, fm, fr, whole in seeds:
            value, error = refine(left, right, fl, fm, fr, whole,
                                  tolerance * (right - left), 0)
            values.append(value)
            errors.append(error)
        return finite(math.fsum(values)), finite(math.fsum(errors))

    def gauss_check(count: int) -> float:
        bounds = _knots(count, 1.23456789)
        contributions = []
        for left, right in zip(bounds, bounds[1:]):
            center, half = (left + right) / 2, (right - left) / 2
            for node, weight in GAUSS8:
                contributions.append(half * weight * sample(center - half * node))
                contributions.append(half * weight * sample(center + half * node))
        return finite(math.fsum(contributions))

    try:
        mean, error = integrate(target)
        final_target = max(settings.abs_tol, settings.rel_tol * abs(mean))
        if error > final_target / 2:
            mean, error = integrate(final_target / 4)
            final_target = max(settings.abs_tol, settings.rel_tol * abs(mean))
        previous = gauss_check(24)
        disagreement = math.inf
        for count in (48, 96, 192, 384, 768, 1536, 3072):
            checked = gauss_check(count)
            disagreement = max(abs(checked - previous), abs(checked - mean))
            if disagreement <= final_target:
                break
            previous = checked
        else:
            raise CalculationError("Los controles independientes no coinciden. No se afirma precisión suficiente.")
        estimate = finite(max(error, disagreement))
        if estimate > final_target:
            raise CalculationError("No se alcanzó la tolerancia del promedio.")
        integral = finite(mean * width, "La integral")
    except (ExpressionError, OverflowError, ValueError) as exc:
        if isinstance(exc, CalculationError):
            raise
        raise CalculationError(str(exc)) from exc
    return Result(function.source, a, b, integral, mean, estimate, len(cache),
                  time.perf_counter() - started, accepted,
                  settings.abs_tol, settings.rel_tol)

def simpson_composite(function: Callable[[float], float], a: float, b: float, n: int) -> float:
    """Versión educativa del método original, con precondiciones explícitas."""
    a, b, width = validate_interval(a, b)
    if type(n) is not int or n <= 0 or n % 2 or n > 1_000_000:
        raise CalculationError("Simpson compuesto requiere n entero positivo y par, hasta 1000000.")
    h = finite(width / n)
    if h <= 0 or a + h == a:
        raise CalculationError("El paso no es representable.")
    values = [finite(function(a)) / 3, finite(function(b)) / 3]
    values.extend((4 / 3 if i % 2 else 2 / 3) * finite(function(a + i * h))
                  for i in range(1, n))
    return finite(h * math.fsum(values))
