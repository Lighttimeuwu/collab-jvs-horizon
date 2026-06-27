"""
utilidades/conexion.py
----------------------
Abre la conexion a boleteria.db resolviendo la ruta de forma robusta,
sin importar desde donde se llame (app.py, VS Code, terminal, etc.).

La BD siempre vive en la raiz del proyecto, junto a app.py:

    raiz/
    ├── app.py
    ├── boleteria.db          ← aqui
    ├── utilidades/
    │   └── conexion.py       ← este archivo
    └── consultas/
        └── *.py
"""

import os
import sqlite3

# __file__ → raiz/utilidades/conexion.py
# dirname  → raiz/utilidades/
# dirname  → raiz/                         ← carpeta del proyecto
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUTA_DB = os.path.join(_RAIZ, "boleteria.db")


def conectar():
    """Devuelve una conexion SQLite a boleteria.db con soporte de FKs activado."""
    conexion = sqlite3.connect(_RUTA_DB)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion