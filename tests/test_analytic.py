"""Referencias externas al algoritmo: antiderivadas y polinomios exactos."""
import math
import random
import unittest
from fractions import Fraction

from average_lab.examples import EXAMPLES
from average_lab.expressions import Expression, parse_bound
from average_lab.numerics import CalculationError, Settings, calculate

class AnalyticTests(unittest.TestCase):
    def test_one_hundred_polynomials_against_exact_fractions(self):
        rng = random.Random(9018)
        for case in range(100):
            a = rng.randint(-3, 1)
            b = rng.randint(a + 1, 4)
            coefficients = [rng.randint(-5, 5) for _ in range(rng.randint(1, 9))]
            source = "+".join(f"({coefficient})*x^{power}"
                              for power, coefficient in enumerate(coefficients))
            exact = sum((Fraction(c * (b ** (i + 1) - a ** (i + 1)), (i + 1) * (b - a))
                         for i, c in enumerate(coefficients)), Fraction(0))
            with self.subTest(case=case, source=source, a=a, b=b):
                result = calculate(Expression.parse(source), a, b)
                self.assertLessEqual(abs(result.average - float(exact)),
                                     max(1e-8, abs(float(exact)) * 1e-8))

    def test_all_examples_at_each_visible_precision(self):
        expected = (3, 2 / math.pi, 5, 0, math.e - 1, 0.5, 2 / 3, 0)
        for example, exact in zip(EXAMPLES, expected):
            for tolerance in (1e-6, 1e-8, 1e-10):
                with self.subTest(example=example.title, tolerance=tolerance):
                    result = calculate(Expression.parse(example.expression),
                                       parse_bound(example.a), parse_bound(example.b),
                                       Settings(abs_tol=tolerance, rel_tol=tolerance))
                    self.assertLessEqual(abs(result.average - exact),
                                         max(tolerance, tolerance * abs(exact)))

    def test_additional_antiderivatives(self):
        cases = [
            ("cos(pi*x)", 0, 1, 0),
            ("cos(x)", -math.pi, math.pi, 0),
            ("sin(3*x+0.2)", -1, 2, (math.cos(-2.8) - math.cos(6.2)) / 9),
            ("exp(-x)", -2, 1, (math.exp(2) - math.exp(-1)) / 3),
            ("ln(x)", 1, math.e, 1 / (math.e - 1)),
            ("1/x", 1, 4, math.log(4) / 3),
            ("sqrt(1-x^2)", -1, 1, math.pi / 4),
            ("1/(1+x^2)", -10, 10, math.atan(10) / 10),
        ]
        for source, a, b, expected in cases:
            with self.subTest(source=source):
                result = calculate(Expression.parse(source), a, b)
                self.assertAlmostEqual(result.average, expected, delta=1e-8)

    def test_huge_cancellation_does_not_claim_unattainable_precision(self):
        with self.assertRaises(CalculationError):
            calculate(Expression.parse("1e300*x"), -1, 1)

    def test_verified_local_zill_section_6_7(self):
        # Comparo con los enunciados de las impresas 353–354, visor 378–379.
        cases = [
            ("x^2", 0, 3, 3),
            ("x^2+1", -2, 2, 7 / 3),
            ("3*x^2-4*x", -1, 3, 3),
            ("sqrt(x)", 0, 9, 2),
            ("cos(2*x)", 0, math.pi / 4, 2 / math.pi),
            ("100+3*x-0.5*x^2", 0, 6, 103),
        ]
        for source, a, b, expected in cases:
            with self.subTest(source=source):
                result = calculate(Expression.parse(source), a, b)
                self.assertAlmostEqual(result.average, expected, delta=1e-8)

if __name__ == "__main__":
    unittest.main()
