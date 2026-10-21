import csv
import json
import math
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path

from average_lab.examples import EXAMPLES
from average_lab.expressions import Expression
from average_lab.gui import AverageApp, export_csv, export_json, sample_curve
from average_lab.numerics import calculate

class ExportTests(unittest.TestCase):
    def test_export_preserves_result_and_samples(self):
        result = calculate(Expression.parse("x^2"), 0, 3)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            export_json(path / "resultado ñ.json", result)
            data = json.loads((path / "resultado ñ.json").read_text(encoding="utf-8"))
            self.assertAlmostEqual(data["average"], 3)
            export_csv(path / "muestras.csv", result)
            with (path / "muestras.csv").open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(len(rows), 502)
            self.assertEqual(float(rows[1][0]), 0)
            self.assertEqual(float(rows[-1][0]), 3)
            self.assertEqual(float(rows[-1][1]), 9)

class GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest("No hay pantalla para Tk: " + str(exc))
        self.root.withdraw()
        self.app = AverageApp(self.root)

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.close()

    def wait_for_result(self):
        deadline = time.monotonic() + 20
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.01)
        self.assertFalse(self.app.busy, "El cálculo no terminó.")

    def test_example_async_result_graph_and_history(self):
        self.app.example.set(EXAMPLES[1].title)
        self.app.load_example()
        self.app.start()
        self.wait_for_result()
        self.assertAlmostEqual(self.app.result.average, 2 / math.pi, places=8)
        self.assertEqual(len(self.app.history), 1)
        self.assertTrue(self.app.canvas.find_withtag("curve"))
        self.assertTrue(self.app.canvas.find_withtag("average"))
        self.app.expression.set("x^2")
        self.assertIsNone(self.app.result)
        self.assertEqual(str(self.app.json_button["state"]), "disabled")
        self.app.history_tree.selection_set("0")
        self.app.restore_history()
        self.assertEqual(self.app.expression.get(), "sin(x)")
        self.assertAlmostEqual(self.app.result.average, 2 / math.pi, places=8)
        self.assertEqual(len(self.app.history), 1)

    def test_invalid_input_then_recovery(self):
        self.app.expression.set("sin(x,1)")
        self.app.start()
        self.assertFalse(self.app.busy)
        self.assertIsNone(self.app.result)
        self.assertIn("Revisa", self.app.status.get())
        self.app.expression.set("sqrt(x)")
        self.app.a.set("-1")
        self.app.start()
        self.wait_for_result()
        self.assertIsNone(self.app.result)
        self.app.load_example()
        self.app.start()
        self.wait_for_result()
        self.assertAlmostEqual(self.app.result.average, 3)

    def test_cancel_discards_result(self):
        self.app.start()
        self.app.cancel()
        self.wait_for_result()
        self.assertIsNone(self.app.result)
        self.assertIn("cancelado", self.app.status.get())

    def test_large_values_graph(self):
        result = calculate(Expression.parse("1e300"), 0, 1)
        self.app.show_result(result)
        self.assertTrue(self.app.canvas.find_withtag("curve"))
        self.assertEqual(len(sample_curve(result)), 361)

if __name__ == "__main__":
    unittest.main()
