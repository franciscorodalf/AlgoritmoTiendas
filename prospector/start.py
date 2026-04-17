"""
start.py
--------
Launcher único: arranca Ollama (si no está corriendo) y el webapp Flask,
luego abre el navegador en la UI.

Uso:
    python start.py

Variables opcionales:
    OLLAMA_BIN     ruta a ollama.exe (default: D:\\Ollama\\bin\\ollama.exe)
    OLLAMA_HOST    default http://localhost:11434
    WEBAPP_PORT    default 5000
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except OSError:
            return False


def ensure_ollama() -> None:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    # parse host:port
    hp = host.replace("http://", "").replace("https://", "").split(":")
    h = hp[0] or "localhost"
    p = int(hp[1]) if len(hp) > 1 else 11434

    if _port_open(h, p):
        print(f"  ✓ Ollama ya corriendo en {host}")
        return

    bin_path = os.getenv("OLLAMA_BIN", r"D:\Ollama\bin\ollama.exe")
    if not Path(bin_path).exists():
        bin_path = shutil.which("ollama") or bin_path
    if not Path(bin_path).exists():
        print(f"  ⚠ No encontré ollama.exe (probé {bin_path}). Arráncalo a mano.")
        return

    print(f"  ▶ Arrancando Ollama desde {bin_path}…")
    creationflags = 0x00000008 if os.name == "nt" else 0  # DETACHED_PROCESS
    subprocess.Popen(
        [bin_path, "serve"],
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Esperar hasta 15s a que abra el puerto
    for _ in range(30):
        if _port_open(h, p):
            print(f"  ✓ Ollama listo en {host}")
            return
        time.sleep(0.5)
    print("  ⚠ Ollama tardó en arrancar — sigo igualmente.")


def main() -> None:
    print("=== PROSPECTOR — launcher ===\n")
    ensure_ollama()

    port = int(os.getenv("WEBAPP_PORT", "5000"))
    url = f"http://127.0.0.1:{port}"
    print(f"\n  ▶ Abriendo UI en {url}\n")

    # Abre el navegador con un pequeño delay para que Flask esté listo
    def _open():
        time.sleep(1.5)
        webbrowser.open(url)
    import threading
    threading.Thread(target=_open, daemon=True).start()

    # Arranca Flask en foreground (bloquea aquí)
    os.environ["WEBAPP_PORT"] = str(port)
    sys.path.insert(0, str(BASE))
    from webapp import main as run_web
    run_web()


if __name__ == "__main__":
    main()
