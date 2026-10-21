import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from average_lab.examples import EXAMPLES
from average_lab.expressions import Expression
from average_lab.gui import AverageApp
from average_lab.numerics import calculate
from average_lab.plotting import Preview, display_formula

class FormulaTests(unittest.TestCase):
    def test_display_changes_not_the_meaning_of_large_exponents(self):
        self.assertEqual(display_formula("x**2+pi*x"),"x²+π·x")
        self.assertEqual(display_formula("x**20+x**2.5"),"x^20+x^2.5")

class PresentationTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root=tk.Tk()
        except tk.TclError as exc:
            self.skipTest(str(exc))
        self.root.withdraw()
        self.app=AverageApp(self.root)

    def tearDown(self):
        if hasattr(self,"app"):
            self.app.close()

    def test_example_selection_loads_and_starts_without_load_button(self):
        self.assertFalse(hasattr(self.app,"load_button"))
        self.app.example.set(EXAMPLES[1].title)
        with patch.object(self.app,"start") as start:
            self.app.example_box.event_generate("<<ComboboxSelected>>")
            self.assertEqual(self.app.expression.get(),"sin(x)")
            self.assertEqual(self.app.b.get(),"pi")
            start.assert_called_once()

    def test_preview_is_not_a_computed_average(self):
        self.app.expression.set("y = sin(x)")
        self.app.preview()
        self.assertIsInstance(self.app.graph.result,Preview)
        self.assertIsNone(self.app.result)
        self.assertIsNone(self.app.graph.result.average)
        self.assertFalse(self.app.canvas.find_withtag("average"))
        self.assertEqual(str(self.app.json_button["state"]),"disabled")
        self.assertTrue(self.app.canvas.find_withtag("curve"))

    def test_comparisons_do_not_replace_active_result(self):
        self.app.pin_curve()
        self.app.expression.set("x")
        result=calculate(Expression.parse("x"),0,3)
        self.app.show_result(result)
        self.assertEqual(len(self.app.comparisons),1)
        self.assertTrue(self.app.canvas.find_withtag("comparison"))
        self.assertIs(self.app.result,result)
        self.assertAlmostEqual(result.average,1.5)
        self.app.remove_curve(0)
        self.assertFalse(self.app.canvas.find_withtag("comparison"))

    def test_fullscreen_exit_keeps_view_and_result(self):
        result=calculate(Expression.parse("x^2"),0,3)
        self.app.show_result(result)
        self.app.toggle_fullscreen()
        self.assertIsNotNone(self.app.presentation_window)
        self.assertIs(self.app.presentation_graph.result,result)
        self.app.presentation_graph.zoom(.7)
        view=self.app.presentation_graph.view
        self.app.leave_fullscreen()
        self.assertIsNone(self.app.presentation_window)
        self.assertIs(self.app.result,result)
        self.assertEqual(self.app.graph.view,view)

    def test_pan_uses_cached_evaluations_and_coalesces_events(self):
        self.app.show_result(calculate(Expression.parse("x^2"),0,3))
        graph=self.app.graph
        with patch("average_lab.plotting.curve_samples",side_effect=AssertionError("Reevaluación innecesaria")):
            for i in range(10):
                graph.view=graph.home.pan(i*.0001,0)
                graph.draw()
        self.assertLess(len(graph.canvas.find_all()),100)
        graph._press(SimpleNamespace(x=100,y=50))
        for i in range(20):
            graph._motion(SimpleNamespace(x=110+i,y=60))
        callback=graph._frame_id
        self.assertIsNotNone(callback)
        graph.request_draw()
        self.assertEqual(graph._frame_id,callback)
        graph._release()
        self.assertIsNone(graph._frame_id)

if __name__=="__main__":
    unittest.main()
