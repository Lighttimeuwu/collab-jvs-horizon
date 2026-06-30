"""
utilidades/conexion.py
----------------------
Abre la conexion a boleteria.db resolviendo la ruta de forma robusta,
funcionando IGUAL tanto en modo desarrollo (`python app.py`) como
empaquetado como .exe con PyInstaller.

CLAVE: boleteria.db se guarda con ruta_persistente(), es decir, en la
carpeta donde esta el .exe real (NO en la carpeta temporal donde
PyInstaller descomprime los recursos). Asi los datos sobreviven entre
ejecuciones y entre actualizaciones del .exe.

Si la base de datos no existe todavia en esa carpeta persistente (por
ejemplo, primera vez que se ejecuta el .exe en una PC nueva), y SI viene
una base de datos "semilla" empaquetada dentro del .exe (ruta_recurso),
se copia automaticamente para que el programa arranque con las tablas
necesarias en vez de fallar.
"""

import os
import shutil
import sqlite3

from utilidades.rutas import ruta_persistente, ruta_recurso

_RUTA_DB = ruta_persistente("boleteria.db")


def _asegurar_db_inicial():
    """
    Si boleteria.db no existe todavia en la carpeta persistente (PC nueva,
    primera ejecucion del .exe), se copia una base "semilla" empaquetada
    dentro del .exe, si existe. Si no hay semilla empaquetada, sqlite3 la
    creara vacia automaticamente al conectar (y el codigo de cada modulo
    ya se encarga de crear sus tablas con CREATE TABLE IF NOT EXISTS).
    """
    if os.path.exists(_RUTA_DB):
        return

    ruta_semilla = ruta_recurso("boleteria.db")
    if os.path.exists(ruta_semilla):
        shutil.copyfile(ruta_semilla, _RUTA_DB)


def conectar():
    """Devuelve una conexion SQLite a boleteria.db con soporte de FKs activado."""
    _asegurar_db_inicial()
    conexion = sqlite3.connect(_RUTA_DB)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion