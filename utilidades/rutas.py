"""
utilidades/rutas.py
--------------------
Resuelve rutas de forma que funcionen IGUAL en dos escenarios:

  1. Ejecutando con `python app.py` (modo desarrollo normal).
  2. Ejecutando el .exe generado con PyInstaller (modo "frozen").

Por que se necesita esto:
--------------------------
Cuando PyInstaller empaqueta el programa en un .exe, en tiempo de
ejecucion extrae todos los archivos agregados (web/, consultas/, etc.)
a una carpeta TEMPORAL distinta en cada PC (sys._MEIPASS), que se borra
al cerrar el programa. Si el codigo sigue usando `__file__` para ubicar
esas carpetas, en la PC del desarrollador "funciona" porque __file__
apunta al proyecto real, pero en el .exe ya empaquetado apunta a esa
carpeta temporal, y si encima la base de datos se guarda ahi, se pierde
cada vez que se cierra el programa.

Por eso separamos dos conceptos:

  - ruta_recurso(...):  para archivos de SOLO LECTURA que van empaquetados
                         dentro del .exe (carpeta web/, plantillas, etc.)
                         Busca primero en sys._MEIPASS (si esta congelado),
                         si no, usa la raiz del proyecto normal.

  - ruta_persistente(...): para archivos que deben sobrevivir entre
                            ejecuciones y ser editables (boleteria.db,
                            imagenes subidas por el usuario, riders, etc.)
                            SIEMPRE usa la carpeta donde esta el .exe real
                            (o la raiz del proyecto si no esta congelado),
                            nunca la carpeta temporal de extraccion.
"""

import os
import sys


def _esta_congelado():
    """True si el programa corre como .exe armado con PyInstaller."""
    return getattr(sys, "frozen", False)


def _raiz_recursos():
    """
    Carpeta donde estan los recursos empaquetados de SOLO LECTURA
    (web/, consultas/, utilidades/, etc.)
    """
    if _esta_congelado():
        # PyInstaller descomprime los --add-data aqui en tiempo de ejecucion.
        return sys._MEIPASS  # type: ignore[attr-defined]
    # Modo desarrollo: dos niveles arriba de este archivo (raiz/utilidades/rutas.py -> raiz/)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _raiz_persistente():
    """
    Carpeta donde deben vivir los archivos que el usuario genera o edita
    (boleteria.db, imagenes subidas, riders, etc.), y que deben sobrevivir
    entre ejecuciones del .exe.
    """
    if _esta_congelado():
        # Carpeta REAL donde esta el .exe (no la temporal de extraccion).
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ruta_recurso(*partes):
    """Ruta absoluta a un recurso empaquetado de solo lectura (ej. web/login/index.html)."""
    return os.path.join(_raiz_recursos(), *partes)


def ruta_persistente(*partes):
    """Ruta absoluta a un archivo que debe persistir junto al .exe (ej. boleteria.db)."""
    carpeta = _raiz_persistente()
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, *partes)