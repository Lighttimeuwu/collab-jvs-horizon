"""
resetear_compras.py
-------------------
Borra todos los datos de compras de la BD y deja la tabla Boleta
con estructura limpia: Boleta_Id | Funcion_Localidad_Id | Usuario_Id

Tablas que se limpian:
    - Evento_Boleta
    - Detalle_Pago
    - Ventas_Web
    - Boleta  (se recrea con columnas limpias)

El resto de la BD (usuarios, eventos, artistas, etc.) no se toca.
"""

import os
import sqlite3

ruta_bd = "boleteria.db" if os.path.exists("boleteria.db") else "../boleteria.db"

if not os.path.exists(ruta_bd):
    print(f"❌ No se encontró la base de datos en: {ruta_bd}")
    exit(1)

confirmacion = input("⚠️  Esto borrará TODAS las compras. ¿Continuar? (s/n): ").strip().lower()
if confirmacion != "s":
    print("Operación cancelada.")
    exit(0)

conexion = sqlite3.connect(ruta_bd)
cursor   = conexion.cursor()
cursor.execute("PRAGMA foreign_keys = OFF")

try:
    # 1. Limpiar tablas de compras
    cursor.execute("DELETE FROM Evento_Boleta")
    cursor.execute("DELETE FROM Detalle_Pago")
    cursor.execute("DELETE FROM Ventas_Web")
    cursor.execute("DELETE FROM Boleta")

    # 2. Resetear autoincrementos
    cursor.execute("""
        DELETE FROM sqlite_sequence
        WHERE name IN ('Boleta', 'Detalle_Pago', 'Ventas_Web', 'Evento_Boleta')
    """)

    # 3. Recrear Boleta con estructura limpia (3 columnas)
    cursor.execute("DROP TABLE Boleta")
    cursor.execute("""
        CREATE TABLE Boleta (
            Boleta_Id            INTEGER PRIMARY KEY AUTOINCREMENT,
            Funcion_Localidad_Id INTEGER,
            Usuario_Id           INTEGER,
            FOREIGN KEY (Funcion_Localidad_Id) REFERENCES Funcion_Localidad(Funcion_Localidad_Id),
            FOREIGN KEY (Usuario_Id)           REFERENCES Usuario(Usuario_Id)
        )
    """)

    conexion.commit()

    print("\n✅ Compras eliminadas correctamente.")
    print("   Boleta_Id            | vacía")
    print("   Funcion_Localidad_Id | vacía")
    print("   Usuario_Id           | vacía")
    print("\n   Detalle_Pago → 0 filas")
    print("   Ventas_Web   → 0 filas")
    print("   Evento_Boleta→ 0 filas")

except Exception as e:
    conexion.rollback()
    print(f"\n❌ Error: {e}")
    raise
finally:
    cursor.execute("PRAGMA foreign_keys = ON")
    conexion.close()