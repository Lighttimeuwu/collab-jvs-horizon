import sqlite3
import os
from tabulate import tabulate

try:
    # Como el archivo está en 'database/', la BD 'boleteria.db' suele estar un nivel arriba.
    # Evaluamos ambas rutas para que funcione sí o sí.
    ruta_bd = "boleteria.db" if os.path.exists("boleteria.db") else "../boleteria.db"
    
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()

    # Obtener el nombre de todas las tablas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()

    if not tablas:
        print("❌ La base de datos está vacía o no se encuentra el archivo 'boleteria.db'.")
    else:
        print(f"📊 TOTAL DE TABLAS DETECTADAS: {len(tablas)}\n")
        
        for tabla in tablas:
            nombre_tabla = tabla[0]
            
            # Obtener nombres de columnas
            cursor.execute(f"PRAGMA table_info({nombre_tabla});")
            columnas = [info[1] for info in cursor.fetchall()]
            
            # Obtener los registros (máximo 5 para visualización rápida)
            cursor.execute(f"SELECT * FROM {nombre_tabla} LIMIT 5;")
            filas = cursor.fetchall()
            
            print(f"📋 TABLA: {nombre_tabla.upper()}")
            if not filas:
                print("   (Esta tabla existe pero está vacía)\n")
            else:
                print(tabulate(filas, headers=columnas, tablefmt="grid"))
                print("\n")

except sqlite3.Error as e:
    print(f"❌ Error en la base de datos: {e}")
finally:
    if 'conexion' in locals():
        conexion.close()