import sqlite3
import os

def conectar():
    # Encuentra la ruta de la carpeta raiz del proyecto de forma absoluta
    ruta_utilidades = os.path.dirname(os.path.abspath(__file__))
    ruta_raiz = os.path.dirname(ruta_utilidades)
    ruta_db = os.path.join(ruta_raiz, "boleteria.db")

    conexion = sqlite3.connect(ruta_db)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion