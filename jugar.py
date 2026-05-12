"""
Lanzador cómodo si abres la terminal dentro de la carpeta ``minesweeper``::

    python jugar.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegura que el directorio padre (donde está el paquete ``minesweeper``) esté en sys.path.
_raiz_paquete = Path(__file__).resolve().parent
_padre = _raiz_paquete.parent
if str(_padre) not in sys.path:
    sys.path.insert(0, str(_padre))

from minesweeper.gui import ejecutar

if __name__ == "__main__":
    ejecutar()
