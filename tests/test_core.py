import contextlib
import importlib
import io
import math
import threading
import unittest
from unittest.mock import patch

from average_lab.expressions import Expression, ExpressionError, parse_bound
from average_lab.numerics import (calculate, simpson_composite, Settings,
                                  CalculationError, CancelledError)

class Expressions(unittest.TestCase):
    def test_valid_syntax_and_aliases(self):
        for source, x, expected in [
            ("x^2+3*x", 2, 10), ("sen(pi/2)+ln(e)", 0, 2),
            ("-sqrt(4)+abs(-3)", 0, 1), ("log10(100)", 0, 2),
            ("cos(π)+tau/τ", 0, 0)]:
            with self.subTest(source=source):
                self.assertAlmostEqual(Expression.parse(source)(x), expected)

    def test_reject_structure_and_arguments_before_evaluation(self):
        for source in ["", "2x", "sin(x,1)", "sin()", "sin(x=1)", "math.sin(x)",
                       "__import__('os')", "[x]", "x[0]", "x if x else 1",
                       "True", "1j", "'text'", "x<1", "sum(x)", "sin", "1e999"]:
            with self.subTest(source=source), self.assertRaises(ExpressionError):
                Expression.parse(source)

    def test_limits_do_not_depend_on_x(self):
        self.assertAlmostEqual(parse_bound("2*pi"), 2*math.pi)
        with self.assertRaises(ExpressionError):
            parse_bound("x+1")

    def test_domains_and_range(self):
        for source in ["1/0", "sqrt(-1)", "log(0)", "exp(1000)", "(-1)^0.5",
                       "10^(10^10)", "tan(pi/2)"]:
            with self.subTest(source=source), self.assertRaises(ExpressionError):
                Expression.parse(source)(0)

    def test_size_limits(self):
        for source in ["x+"*200+"x", "-"*30+"x"]:
            with self.assertRaises(ExpressionError):
                Expression.parse(source)

    def test_import_has_no_input(self):
        with patch("builtins.input", side_effect=AssertionError("input al importar")):
            importlib.reload(importlib.import_module("main"))

class Integration(unittest.TestCase):
    def check_mean(self, expression, a, b, exact, tolerance=1e-7):
        result=calculate(Expression.parse(expression),a,b)
        self.assertLessEqual(abs(result.average-exact),tolerance)
        self.assertTrue(math.isfinite(result.integral))
        self.assertLessEqual(result.estimated_error,
                             max(result.abs_tol,result.rel_tol*abs(result.average)))
        return result

    def test_reference_cases(self):
        for source,a,b,exact in [
            ("5",-2,4,5), ("-5",0,1,-5), ("x^2",0,3,3), ("x^3",-2,2,0),
            ("sin(x)",0,math.pi,2/math.pi), ("exp(x)",0,1,math.e-1),
            ("abs(x)",-1,1,.5), ("sqrt(x)",0,1,2/3),
            ("1/(1+x^2)",0,1,math.pi/4)]:
            with self.subTest(source=source):
                self.check_mean(source,a,b,exact)

    def test_regression_uniform_mesh_aliasing(self):
        f=Expression.parse("cos(800*pi*x)")
        self.assertAlmostEqual(simpson_composite(f,0,1,200),1)
        self.assertAlmostEqual(simpson_composite(f,0,1,400),1)
        self.check_mean(f.source,0,1,0)

    def test_shifted_peak(self):
        self.check_mean("exp(-((x-0.4137)/0.015)^2)",0,1,
                        math.sqrt(math.pi)*.015)

    def test_small_interval_mean_tolerance(self):
        self.check_mean("sqrt(x/0.0001)",0,1e-4,2/3)

    def test_invalid_intervals(self):
        for a,b in [(0,0),(2,1),(-1e308,1e308),(math.nan,1),(0,math.inf),
                    (1e16,1e16+2)]:
            with self.subTest(a=a,b=b), self.assertRaises((CalculationError,ExpressionError)):
                calculate(Expression.parse("1"),a,b)

    def test_nonfinite_integral(self):
        with self.assertRaises(CalculationError):
            calculate(Expression.parse("1e308"),0,10)

    def test_invalid_domain_and_pole(self):
        for source,a,b in [("sqrt(x)",-1,1),("log(x)",0,1),("1/x",-1,1),
                           ("1/(x-0.3)",0,1)]:
            with self.subTest(source=source), self.assertRaises(CalculationError):
                calculate(Expression.parse(source),a,b)

    def test_cancellation(self):
        event=threading.Event();event.set()
        with self.assertRaises(CancelledError):
            calculate(Expression.parse("x"),0,1,cancel=event)

    def test_budget_is_enforced(self):
        with self.assertRaises(CalculationError):
            calculate(Expression.parse("sin(3000*x)"),0,1,
                      Settings(max_evaluations=100))

    def test_composite_requires_even_positive_integer(self):
        for n in [0,-2,3,2.5,True]:
            with self.assertRaises(CalculationError):
                simpson_composite(lambda x:x,0,1,n)
        self.assertAlmostEqual(simpson_composite(lambda x:x**3,0,2,10),4)

    def test_settings(self):
        for settings in [Settings(abs_tol=0), Settings(rel_tol=math.nan),
                         Settings(max_depth=0),Settings(time_limit=0)]:
            with self.assertRaises((CalculationError,ExpressionError)):
                calculate(Expression.parse("x"),0,1,settings)

    def test_cli_can_correct_error_and_continue(self):
        from average_lab.cli import run
        with patch("builtins.input",side_effect=["sqrt(x)","-1","1","x^2","0","3","salir"]):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                run()
        self.assertIn("No se pudo calcular",output.getvalue())
        self.assertIn("Valor promedio: 3",output.getvalue())

if __name__ == "__main__":
    unittest.main()
