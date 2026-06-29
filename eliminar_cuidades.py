import os
import sqlite3

def purgar_rastro_ciudad():
    # Encontrar la ruta exacta de la base de datos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "boleteria.db")
    
    if not os.path.exists(db_path):
        print(f"❌ No se encontró la base de datos en: {db_path}")
        return

    print(f"🔗 Conectando a la base de datos: {db_path}")
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    try:
        # 1. Intentar borrar la columna 'Ciudad' de la tabla Usuario
        try:
            cursor.execute("ALTER TABLE Usuario DROP COLUMN Ciudad;")
            print("  ✓ Columna 'Ciudad' eliminada de la tabla 'Usuario'.")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️ Tabla 'Usuario': {e} (Probablemente ya no existe).")

        # 2. Intentar borrar la columna 'Ciudad' de la tabla Funcion
        try:
            cursor.execute("ALTER TABLE Funcion DROP COLUMN Ciudad;")
            print("  ✓ Columna 'Ciudad' eliminada de la tabla 'Funcion'.")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️ Tabla 'Funcion': {e} (Probablemente ya no existe).")

        # 3. Borrar tablas residuales si es que existían
        cursor.execute("DROP TABLE IF EXISTS Ciudad;")
        cursor.execute("DROP TABLE IF EXISTS Ciudades;")
        print("  ✓ Tablas independientes de 'Ciudad' o 'Ciudades' eliminadas (si existían).")

        # Guardar cambios
        conexion.commit()
        print("\n🎉 ¡Éxito! Todo rastro estructural de 'Ciudad' ha sido borrado de la base de datos.")

    except Exception as error:
        conexion.rollback()
        print(f"\n❌ Error general durante la ejecución: {error}")
        
    finally:
        conexion.close()

if __name__ == "__main__":
    print("🧹 Iniciando purga del campo 'Ciudad'...")
    purgar_rastro_ciudad()