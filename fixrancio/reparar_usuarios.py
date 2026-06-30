import os
import sqlite3
import random

def reparar_usuarios_legacy():
    # Detectar la ruta de la base de datos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "boleteria.db")
    
    if not os.path.exists(db_path):
        print(f"❌ No se encontró el archivo 'boleteria.db' en: {db_path}")
        return

    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    # Pool de ciudades para asignar aleatoriamente
    ciudades_disponibles = ["Bogotá"]

    try:
        # 1. Buscamos solo los usuarios que tengan Correo, Teléfono o Ciudad en NULL
        cursor.execute("""
            SELECT Usuario_Id, Nombre, Apellido 
            FROM Usuario 
            WHERE Correo IS NULL OR Telefono IS NULL OR Ciudad IS NULL
        """)
        usuarios_afectados = cursor.fetchall()

        if not usuarios_afectados:
            print("✨ ¡Excelente! No se encontraron usuarios con campos NULL.")
            return

        print(f"🔄 Se encontraron {len(usuarios_afectados)} usuarios antiguos con datos NULL. Procesando...")

        for usuario in usuarios_afectados:
            usuario_id, nombre, apellido = usuario

            # Limpiamos espacios y caracteres extraños para armar un correo limpio
            nombre_clean = "".join(c for c in nombre.lower() if c.isalnum())
            apellido_clean = "".join(c for c in apellido.lower() if c.isalnum())

            # --- REGLA DE INTEGRIDAD: CUMPLIENDO LA UNICIDAD ---
            # Mezclamos el nombre con su ID único para asegurar que JAMÁS se repita un correo
            correo_generado = f"{nombre_clean}.{apellido_clean}{usuario_id}@testanime.com"
            
            # Generamos un teléfono de 10 dígitos único usando el ID al final (ej: ID 42 -> 3000000042)
            telefono_generado = f"300{usuario_id:07d}"
            
            # Seleccionamos una ciudad al azar
            ciudad_aleatoria = random.choice(ciudades_disponibles)

            # 2. Actualizamos al usuario usando COALESCE por si acaso ya tenía alguno de los campos lleno
            cursor.execute("""
                UPDATE Usuario
                SET Correo = COALESCE(Correo, ?),
                    Telefono = COALESCE(Telefono, ?),
                    Ciudad = COALESCE(Ciudad, ?)
                WHERE Usuario_Id = ?
            """, (correo_generado, telefono_generado, ciudad_aleatoria, usuario_id))

            print(f"  ✓ ID {usuario_id} [{nombre} {apellido}]: Correo: {correo_generado} | Tel: {telefono_generado} | Ciudad: {ciudad_aleatoria}")

        # Guardar cambios permanentemente
        conexion.commit()
        print("\n🎉 ¡Éxito! Todos los usuarios antiguos han sido reparados y ya cumplen las reglas del sistema.")

    except Exception as error:
        conexion.rollback()
        print(f"❌ Ocurrió un error al intentar reparar los usuarios: {error}")
    finally:
        conexion.close()

if __name__ == "__main__":
    reparar_usuarios_legacy()