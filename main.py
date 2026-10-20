"""Entrada de Function Average Lab. Prototipo original: Rodrigo Polanco.

La evolución modular conserva Simpson y el intérprete AST, con asistencia de
Codex documentada en AUTHORS.md. Importar este archivo no solicita entradas.
"""
from __future__ import annotations
import argparse
import json

def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula el valor promedio de una función.")
    parser.add_argument("--cli", action="store_true", help="Abrir la consola educativa.")
    parser.add_argument("--self-test", action="store_true", help="Verificar el motor y terminar.")
    args = parser.parse_args()
    if args.self_test:
        from average_lab.cli import self_test
        print(json.dumps(self_test(), ensure_ascii=False))
    else:
        from average_lab.cli import run
        run()

if __name__ == "__main__":
    main()
