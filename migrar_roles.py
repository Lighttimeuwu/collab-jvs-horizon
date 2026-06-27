"""
migrar_roles.py
----------------
Migracion para boleteria.db:

1. Crea la tabla Usuario_Rol (Usuario_Id, Rol_Id) con FK real a Usuario y Rol.
   Esta tabla reemplaza el uso indebido de Administrador_Rol para vincular
   roles a usuarios (esa tabla tiene FK a Administrador, que solo tiene 1 fila
   y no corresponde a Usuario_Id). Un usuario PUEDE tener varios roles a la
   vez aqui (ej. Cliente + Coordinador), y Usuario_Rol sigue siendo la unica
   fuente de verdad real para "que roles tiene cada usuario".
2. Inserta el rol "Cliente" (Rol_Id = 4) en la tabla Rol si no existe.
3. Asigna Rol_Id = 4 (Cliente) a TODOS los usuarios que ya existen en el
   sistema y que todavia no tengan ningun rol asignado en Usuario_Rol.
4. Agrega la columna Rol_Id a la tabla Usuario (si no existe). Esta columna
   es una CACHE/VISTA RAPIDA, no la fuente de verdad: siempre refleja el rol
   mas relevante del usuario segun Usuario_Rol (1=Administrador es el mas
   relevante, 4=Cliente el menos). Si el usuario tiene varios roles, aqui se
   guarda el de menor Rol_Id. Esta columna existe solo para que el rol sea
   visible de un vistazo al abrir la tabla Usuario; cualquier cambio de roles
   debe seguir haciendose en Usuario_Rol, y luego sincronizar esta columna
   (ver sincronizar_rol_id_en_usuario(), tambien expuesta para reutilizar
   despues de inserciones/eliminaciones manuales en Usuario_Rol).

A partir de esta migracion, los roles se manejan UNICAMENTE con las tablas
Usuario, Rol y Usuario_Rol (mas la columna cache Usuario.Rol_Id). Las tablas
Administrador y Administrador_Rol quedan DEPRECADAS por decision explicita:
no se eliminan ni se modifican (se dejan existir vacias/intactas como
estaban, por precaucion), pero ningun archivo del proyecto vuelve a leerlas
ni escribirlas.

Es seguro ejecutar este script mas de una vez: no duplica roles ni usuarios
ya migrados (usa INSERT OR IGNORE / verificaciones previas), y siempre
vuelve a sincronizar la columna cache Usuario.Rol_Id por si hubo cambios
manuales en Usuario_Rol desde la ultima corrida.

Uso:
    python3 migrar_roles.py
"""

import os
import sys

ruta_raiz = os.path.dirname(os.path.abspath(__file__))
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar

ROL_CLIENTE_ID = 4
ROL_CLIENTE_NOMBRE = "Cliente"


def crear_tabla_usuario_rol(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuario_Rol (
            Usuario_Id INTEGER NOT NULL,
            Rol_Id     INTEGER NOT NULL,
            PRIMARY KEY (Usuario_Id, Rol_Id),
            FOREIGN KEY (Usuario_Id) REFERENCES Usuario(Usuario_Id),
            FOREIGN KEY (Rol_Id)     REFERENCES Rol(Rol_Id)
        )
    """)
    print("✔ Tabla Usuario_Rol verificada/creada.")


def asegurar_rol_cliente(cursor):
    cursor.execute("SELECT Rol_Id FROM Rol WHERE Rol_Id = ?", (ROL_CLIENTE_ID,))
    if cursor.fetchone():
        print(f"✔ Rol Cliente (Id={ROL_CLIENTE_ID}) ya existe.")
        return

    cursor.execute(
        "INSERT INTO Rol (Rol_Id, Nombre_Rol) VALUES (?, ?)",
        (ROL_CLIENTE_ID, ROL_CLIENTE_NOMBRE)
    )
    print(f"✔ Rol Cliente (Id={ROL_CLIENTE_ID}) insertado.")


def asegurar_columna_rol_en_usuario(cursor):
    """Agrega Usuario.Rol_Id (columna cache) si no existe todavia."""
    columnas = {fila[1] for fila in cursor.execute("PRAGMA table_info(Usuario)").fetchall()}
    if "Rol_Id" in columnas:
        print("✔ Columna Usuario.Rol_Id ya existe.")
        return

    cursor.execute("ALTER TABLE Usuario ADD COLUMN Rol_Id INTEGER REFERENCES Rol(Rol_Id)")
    print("✔ Columna Usuario.Rol_Id agregada.")


def sincronizar_rol_id_en_usuario(cursor):
    """
    Recalcula Usuario.Rol_Id para TODOS los usuarios a partir de Usuario_Rol,
    tomando el rol mas relevante (el de menor Rol_Id) cuando un usuario tiene
    varios. Si un usuario no tiene ninguna fila en Usuario_Rol, su Rol_Id
    queda en NULL (no deberia pasar tras correr este script, pero se cubre
    el caso por seguridad).
    """
    cursor.execute("""
        UPDATE Usuario
        SET Rol_Id = (
            SELECT MIN(UR.Rol_Id)
            FROM Usuario_Rol UR
            WHERE UR.Usuario_Id = Usuario.Usuario_Id
        )
    """)
    print(f"✔ Columna Usuario.Rol_Id sincronizada para {cursor.rowcount} usuario(s).")


def asignar_rol_cliente_a_usuarios_sin_rol(cursor):
    cursor.execute("""
        SELECT U.Usuario_Id
        FROM Usuario U
        LEFT JOIN Usuario_Rol UR ON U.Usuario_Id = UR.Usuario_Id
        WHERE UR.Usuario_Id IS NULL
    """)
    usuarios_sin_rol = [fila[0] for fila in cursor.fetchall()]

    if not usuarios_sin_rol:
        print("✔ Todos los usuarios ya tienen un rol asignado. Nada que hacer.")
        return

    cursor.executemany(
        "INSERT OR IGNORE INTO Usuario_Rol (Usuario_Id, Rol_Id) VALUES (?, ?)",
        [(usuario_id, ROL_CLIENTE_ID) for usuario_id in usuarios_sin_rol]
    )
    print(f"✔ Rol Cliente asignado a {len(usuarios_sin_rol)} usuario(s): {usuarios_sin_rol}")


def main():
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        crear_tabla_usuario_rol(cursor)
        asegurar_rol_cliente(cursor)
        asignar_rol_cliente_a_usuarios_sin_rol(cursor)
        asegurar_columna_rol_en_usuario(cursor)
        sincronizar_rol_id_en_usuario(cursor)
        conexion.commit()
        print("\n✅ Migracion completada correctamente.")
    except Exception as error:
        conexion.rollback()
        print(f"\n❌ Error durante la migracion, se revirtio todo: {error}")
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
