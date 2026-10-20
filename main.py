"""Entrada de Function Average Lab. Prototipo original: Rodrigo Polanco.

La evolución modular conserva Simpson y el intérprete AST, con asistencia de
Codex documentada en AUTHORS.md. Importar este archivo no solicita entradas.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula el valor promedio de una función.")
    parser.add_argument("--cli", action="store_true", help="Abrir la consola educativa.")
    parser.add_argument("--self-test", action="store_true", help="Verificar el motor y terminar.")
    parser.add_argument("--smoke-test", action="store_true", help="Verificar motor e interfaz y terminar.")
    parser.add_argument("--report", type=Path, help="Guardar el informe de verificación en JSON.")
    args = parser.parse_args()
    if args.self_test or args.smoke_test:
        if args.smoke_test:
            from average_lab.gui import smoke_test
            report = smoke_test()
        else:
            from average_lab.cli import self_test
            report = self_test()
        data = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        if args.report:
            args.report.write_text(data + "\n", encoding="utf-8")
        # El ejecutable de ventana no tiene salida estándar asociada.
        import sys
        if sys.stdout is not None:
            print(data)
    elif args.cli:
        from average_lab.cli import run
        run()
    else:
        from average_lab.gui import run
        run()

if __name__ == "__main__":
    main()
