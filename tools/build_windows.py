"""Construye, comprueba y empaqueta la aplicación. Ejecutar desde Windows."""
from __future__ import annotations
import hashlib
import json
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build():
    if platform.system() != "Windows":
        raise SystemExit("El ejecutable Windows debe construirse en Windows.")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onefile", "--windowed", "--name", "FunctionAverageLab",
                    "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
                    "--specpath", str(ROOT / "build"), str(ROOT / "main.py")],
                   cwd=ROOT, check=True)
    exe = ROOT / "dist" / "FunctionAverageLab.exe"
    report = ROOT / "dist" / "verificacion-ejecutable.json"
    # Se prueba el archivo congelado desde otra carpeta: no debe depender del código fuente.
    subprocess.run([str(exe), "--smoke-test", "--report", str(report)],
                   cwd=ROOT / "dist", check=True, timeout=90)
    data = json.loads(report.read_text(encoding="utf-8"))
    if not data.get("ok") or abs(data["average"] - 3) > 1e-8:
        raise SystemExit("El ejecutable no superó su comprobación.")
    (ROOT / "dist" / "SHA256SUMS.txt").write_text(
        hashlib.sha256(exe.read_bytes()).hexdigest() + "  " + exe.name + "\n", encoding="ascii")
    archive = ROOT / "dist" / "FunctionAverageLab-Windows.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for path in (exe, report, ROOT / "dist" / "SHA256SUMS.txt", ROOT / "README.md", ROOT / "AUTHORS.md"):
            output.write(path, path.name)
        for path in sorted((ROOT / "docs").glob("*.md")):
            output.write(path, "docs/" + path.name)
    print(json.dumps({"exe": exe.name, "portable": archive.name, "smoke_test": data},
                     ensure_ascii=True, indent=2))

if __name__ == "__main__":
    build()
