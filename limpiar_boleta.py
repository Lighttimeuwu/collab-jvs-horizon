"""
limpiar_boleta.py
-----------------
Deja la tabla Boleta solo con las columnas que debe tener:
    Boleta_Id             INTEGER PRIMARY KEY
    Funcion_Localidad_Id  INTEGER  (FK → Funcion_Localidad)
    Usuario_Id            INTEGER  (FK → Usuario — quién compró)

Elimina cualquier columna de texto que haya quedado de versiones anteriores
(Usuario_Correo, Usuario_Nombre, Evento, Fecha_Evento, Lugar, Asientos,
Cantidad, Total, Fecha_Compra).

SQLite no soporta DROP COLUMN en versiones < 3.35, así que usamos el método
estándar: crear tabla nueva → copiar datos → renombrar.
"""

import os
import sys
import sqlite3

# Funciona tanto desde la carpeta raíz como desde subcarpetas
ruta_bd = "boleteria.db" if os.path.exists("boleteria.db") else "../boleteria.db"

conexion = sqlite3.connect(ruta_bd)
cursor   = conexion.cursor()
cursor.execute("PRAGMA foreign_keys = OFF")   # desactivar FKs durante la migración

try:
    # 1. Ver columnas actuales
    cursor.execute("PRAGMA table_info(Boleta)")
    columnas_actuales = [fila[1] for fila in cursor.fetchall()]
    print(f"Columnas actuales en Boleta: {columnas_actuales}")

    # 2. Crear tabla limpia con exactamente las tres columnas correctas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Boleta_Limpia (
            Boleta_Id            INTEGER PRIMARY KEY AUTOINCREMENT,
            Funcion_Localidad_Id INTEGER,
            Usuario_Id           INTEGER,
            FOREIGN KEY (Funcion_Localidad_Id) REFERENCES Funcion_Localidad(Funcion_Localidad_Id),
            FOREIGN KEY (Usuario_Id)           REFERENCES Usuario(Usuario_Id)
        )
    """)

    # 3. Copiar solo las columnas que existen en ambas tablas
    cols_a_copiar = [c for c in ["Boleta_Id", "Funcion_Localidad_Id", "Usuario_Id"]
                     if c in columnas_actuales]
    cols_str = ", ".join(cols_a_copiar)
    cursor.execute(f"INSERT INTO Boleta_Limpia ({cols_str}) SELECT {cols_str} FROM Boleta")
    filas_copiadas = cursor.rowcount
    print(f"Filas copiadas: {filas_copiadas}")

    # 4. Borrar tabla vieja y renombrar
    cursor.execute("DROP TABLE Boleta")
    cursor.execute("ALTER TABLE Boleta_Limpia RENAME TO Boleta")

    conexion.commit()
    print("\n✅ Tabla Boleta limpiada correctamente.")
    print("   Columnas finales: Boleta_Id | Funcion_Localidad_Id | Usuario_Id")

    # 5. Verificar resultado
    cursor.execute("PRAGMA table_info(Boleta)")
    print("\nEstructura final:")
    for col in cursor.fetchall():
        print(f"   {col[1]} {col[2]}")

    cursor.execute("SELECT COUNT(*) FROM Boleta")
    print(f"\nTotal de filas en Boleta: {cursor.fetchone()[0]}")

except Exception as e:
    conexion.rollback()
    print(f"❌ Error durante la migración: {e}")
    raise
finally:
    cursor.execute("PRAGMA foreign_keys = ON")
    conexion.close()