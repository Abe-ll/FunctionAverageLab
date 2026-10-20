import math
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from average_lab.expressions import Expression, parse_bound
from average_lab.gui import AverageApp
from average_lab.numerics import calculate
from average_lab.plotting import Viewport, axis_label, clip_line, curve_samples, export_png, fit_view, scene
from average_lab.themes import THEMES

class PlotTests(unittest.TestCase):
    def setUp(self):
        self.result = calculate(Expression.parse("x^2"), 0, 3)

    def test_zoom_keeps_the_point_under_the_cursor(self):
        view = fit_view(self.result)
        zoomed = view.zoom(0.5, 0.25, 0.7)
        self.assertAlmostEqual(view.left + (view.right-view.left)*0.25,
                               zoomed.left + (zoomed.right-zoomed.left)*0.25)
        self.assertAlmostEqual(view.bottom + (view.top-view.bottom)*0.7,
                               zoomed.bottom + (zoomed.top-zoomed.bottom)*0.7)
        self.assertAlmostEqual(zoomed.right-zoomed.left, (view.right-view.left)/2)
        self.assertEqual(view.zoom(1e-30), view)
        with self.assertRaises(ValueError):
            view.zoom(0)

    def test_zoom_resamples_the_visible_interval(self):
        wide = curve_samples(self.result, 0, 1, 401)
        near = curve_samples(self.result, .49, .51, 401)
        self.assertLess(near[1][0]-near[0][0], wide[1][0]-wide[0][0])
        self.assertAlmostEqual(near[200][1], 2.25)
        self.assertEqual(curve_samples(self.result, 2, 3), [])

    def test_deep_zoom_labels_and_float_resolution(self):
        self.assertNotEqual(axis_label(1.5, 1e-9), axis_label(1.500000001, 1e-9))
        view = Viewport(1e7, 1e7+1, 0, 1, 1)
        for _ in range(80):
            view = view.zoom(.5)
        self.assertGreater(view.right, view.left)
        self.assertGreater(view.top, view.bottom)

    def test_segments_are_clipped_at_plot_edges(self):
        self.assertEqual(clip_line(-10, 5, 30, 5, 20, 10), (0, 5, 20, 5))
        self.assertIsNone(clip_line(-10, -5, -1, -5, 20, 10))
        view = fit_view(self.result).zoom(.05)
        for item in scene(self.result, view, 800, 500, THEMES["light"]):
            if item[0] == "line" and item[4] == "curve":
                self.assertTrue(all(82-1e-5 <= x <= 776+1e-5 for x in item[1][::2]))
                self.assertTrue(all(26-1e-5 <= y <= 456+1e-5 for y in item[1][1::2]))

    def test_png_is_real_image_in_current_theme_and_view(self):
        view = fit_view(self.result)
        with tempfile.TemporaryDirectory() as temp:
            files = []
            for name in ("light", "dark"):
                path = Path(temp) / (name + " ñ.png")
                export_png(path, self.result, view, THEMES[name])
                with Image.open(path) as image:
                    self.assertEqual(image.format, "PNG")
                    self.assertEqual(image.size, (1600, 1000))
                    color = THEMES[name]["card"]
                    expected = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                    self.assertEqual(image.getpixel((0, 0)), expected)
                    self.assertGreater(len(image.getcolors(2_000_000)), 30)
                files.append(path.read_bytes())
            self.assertNotEqual(*files)
            zoom = Path(temp) / "zoom.png"
            export_png(zoom, self.result, view.zoom(.5), THEMES["light"], grid=False)
            self.assertNotEqual(zoom.read_bytes(), files[0])

class InteractionTests(unittest.TestCase):
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

    def result(self):
        self.app.show_result(calculate(Expression.parse("x^2"), 0, 3))

    def test_theme_switch_keeps_result_and_history(self):
        self.result()
        result = self.app.result
        self.app.toggle_theme()
        self.assertEqual(self.app.theme_name, "dark")
        self.assertEqual(self.app.canvas["background"], THEMES["dark"]["card"])
        self.assertEqual(self.app.steps["foreground"], THEMES["dark"]["ink"])
        self.assertIs(self.app.result, result)
        self.assertEqual(len(self.app.history), 1)
        self.app.toggle_theme()
        self.assertEqual(self.app.theme_name, "light")
        self.assertIs(self.app.result, result)

    def test_pan_scroll_slider_grid_and_reset_do_not_recalculate(self):
        self.result()
        graph = self.app.graph
        home, result = graph.home, self.app.result
        graph.zoom(.5)
        self.assertAlmostEqual(graph.view.right-graph.view.left, (home.right-home.left)/2)
        graph.scroll("x", "scroll", 1, "units")
        self.assertNotEqual(graph.view.left, home.left)
        graph.scroll("y", "moveto", .3)
        self.assertNotEqual(graph.view.top, home.top)
        graph._slide("2")
        self.assertAlmostEqual(graph.view.right-graph.view.left, (home.right-home.left)/4)
        graph.grid_visible.set(False)
        graph.draw()
        self.assertFalse(graph.canvas.find_withtag("grid"))
        graph.grid_visible.set(True)
        graph.draw()
        self.assertTrue(graph.canvas.find_withtag("grid"))
        graph._press(SimpleNamespace(x=100, y=60))
        old = graph.view
        graph._motion(SimpleNamespace(x=110, y=70))
        self.assertNotEqual(graph.view, old)
        graph.fit()
        self.assertEqual(graph.view, home)
        self.assertIs(self.app.result, result)
        self.assertEqual(len(self.app.history), 1)

    def test_keyboard_functions_selection_and_multiplication(self):
        entry = self.app.function_entry
        entry.delete(0, "end")
        self.app.keyboard.show(entry)
        keys = self.app.keyboard
        keys.buttons["√"].invoke()
        keys.press("9")
        self.assertEqual(entry.get(), "sqrt(9)")
        self.assertEqual(Expression.parse(entry.get())(), 3)
        entry.selection_range(0, "end")
        keys.press("cos")
        self.assertEqual(entry.get(), "cos(sqrt(9))")
        keys.press("AC")
        for key in ("2", "π", "x"):
            keys.press(key)
        self.assertEqual(entry.get(), "2*pi*x")
        self.assertAlmostEqual(Expression.parse(entry.get())(1), 2*math.pi)
        keys.press("AC")
        keys.press("x²")
        self.assertEqual(entry.get(), "x^2")
        entry.selection_range(0, "end")
        keys.press("a⁄b")
        keys.press("2")
        self.assertEqual(entry.get(), "(x^2)/(2)")
        self.assertEqual(Expression.parse(entry.get())(4), 8)

    def test_keyboard_limits_editing_and_disabled_input(self):
        self.result()
        entry = self.app.b_entry
        entry.delete(0, "end")
        self.app.keyboard.show(entry)
        for key in ("π", "÷", "2"):
            self.app.keyboard.press(key)
        self.assertAlmostEqual(parse_bound(self.app.b.get()), math.pi/2)
        self.assertIsNone(self.app.result)
        self.assertEqual(str(self.app.image_button["state"]), "disabled")
        entry.icursor(0)
        self.app.keyboard.press("⌫")
        self.assertEqual(entry.get(), "pi/2")
        self.app._busy(True)
        self.app.keyboard.press("9")
        self.assertEqual(entry.get(), "pi/2")
        self.app._busy(False)

    def test_png_button_cancel_and_save(self):
        self.result()
        self.app.toggle_theme()
        with tempfile.TemporaryDirectory() as temp:
            target = str(Path(temp) / "gráfica ñ.png")
            with patch("average_lab.gui.filedialog.asksaveasfilename", return_value=""):
                self.app.save_image()
            self.assertFalse(Path(target).exists())
            with patch("average_lab.gui.filedialog.asksaveasfilename", return_value=target):
                self.app.image_button.invoke()
            self.assertTrue(Path(target).is_file())
            with Image.open(target) as image:
                self.assertEqual(image.format, "PNG")

if __name__ == "__main__":
    unittest.main()
