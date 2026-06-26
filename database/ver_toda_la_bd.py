import sqlite3
import os
from tabulate import tabulate

try:
    ruta_bd = "boleteria.db" if os.path.exists("boleteria.db") else "../boleteria.db"
    
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()

    # ── Sección especial: Boletas con comprador ──────────────────────────────
    print("=" * 70)
    print("🎟️  BOLETAS CON DATOS DE COMPRADOR")
    print("=" * 70)
    try:
        cursor.execute("PRAGMA table_info(Boleta)")
        cols_boleta = {fila[1] for fila in cursor.fetchall()}
        if "Usuario_Id" in cols_boleta:
            cursor.execute("""
                SELECT B.Boleta_Id,
                       B.Usuario_Id,
                       U.Nombre || ' ' || U.Apellido AS Comprador,
                       U.Correo                      AS Correo,
                       B.Evento,
                       B.Fecha_Evento  AS Fecha,
                       B.Lugar,
                       B.Asientos,
                       B.Cantidad,
                       B.Total,
                       B.Fecha_Compra  AS Fecha_Compra
                FROM Boleta B
                LEFT JOIN Usuario U ON B.Usuario_Id = U.Usuario_Id
                WHERE B.Usuario_Id IS NOT NULL
                ORDER BY B.Boleta_Id DESC
                LIMIT 20
            """)
            filas = cursor.fetchall()
            headers = ["ID Boleta", "ID Usuario", "Comprador", "Correo", "Evento",
                       "Fecha", "Lugar", "Asientos", "Cant", "Total", "Fecha Compra"]
            if filas:
                print(tabulate(filas, headers=headers, tablefmt="grid"))
            else:
                print("   (Aún no hay compras registradas con datos de usuario)\n")
        else:
            print("   (La columna Usuario_Id aún no existe en Boleta)\n")
            print("   Ejecuta el servidor Flask y realiza una compra para generarla.\n")
    except Exception as e:
        print(f"   Nota: {e}\n")
    print()

    # ── Resto de tablas ──────────────────────────────────────────────────────
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()

    if not tablas:
        print("❌ La base de datos está vacía o no se encuentra el archivo 'boleteria.db'.")
    else:
        print(f"📊 TOTAL DE TABLAS DETECTADAS: {len(tablas)}\n")
        
        for tabla in tablas:
            nombre_tabla = tabla[0]
            
            cursor.execute(f"PRAGMA table_info({nombre_tabla});")
            columnas = [info[1] for info in cursor.fetchall()]
            
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