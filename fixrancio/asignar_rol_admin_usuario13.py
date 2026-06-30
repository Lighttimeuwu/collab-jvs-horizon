"""
asignar_rol_admin_usuario13.py
-------------------------------
Asigna el rol Administrador (Rol_Id = 1) al usuario con Usuario_Id = 13,
sin quitarle los roles que ya tenga (ej. Cliente). Sincroniza tambien la
columna cache Usuario.Rol_Id.

Uso:
    python3 asignar_rol_admin_usuario13.py
"""

import os
import sys

ruta_raiz = os.path.dirname(os.path.abspath(__file__))
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar
from consultas.usuarios import (
    asegurar_tabla_usuario_rol,
    asegurar_columna_rol_en_usuario,
    sincronizar_rol_id_usuario,
)

USUARIO_ID = 13
ROL_ADMIN_ID = 1


def main():
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_usuario_rol(cursor)
        asegurar_columna_rol_en_usuario(cursor)

        cursor.execute(
            "INSERT OR IGNORE INTO Usuario_Rol (Usuario_Id, Rol_Id) VALUES (?, ?)",
            (USUARIO_ID, ROL_ADMIN_ID)
        )
        sincronizar_rol_id_usuario(cursor, USUARIO_ID)

        conexion.commit()

        cursor.execute("SELECT Usuario_Id, Nombre, Apellido, Rol_Id FROM Usuario WHERE Usuario_Id = ?", (USUARIO_ID,))
        print("Usuario actualizado:", cursor.fetchone())

        cursor.execute("SELECT * FROM Usuario_Rol WHERE Usuario_Id = ?", (USUARIO_ID,))
        print("Roles que tiene ahora:", cursor.fetchall())

    except Exception as error:
        conexion.rollback()
        print(f"❌ Error: {error}")
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
