import sys
import os

# Agregamos la carpeta raiz al sistema para que encuentre 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

# Ahora el import funcionara siempre, uses o no el boton de Play de VS Code
from utilidades.conexion import conectar


ROL_CLIENTE_ID = 4
ROLES_VALIDOS = {1, 2, 3, 4}


def asegurar_tabla_usuario_rol(cursor):
    """Crea Usuario_Rol si no existe (misma forma que usa migrar_roles.py)."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuario_Rol (
            Usuario_Id INTEGER NOT NULL,
            Rol_Id     INTEGER NOT NULL,
            PRIMARY KEY (Usuario_Id, Rol_Id),
            FOREIGN KEY (Usuario_Id) REFERENCES Usuario(Usuario_Id),
            FOREIGN KEY (Rol_Id)     REFERENCES Rol(Rol_Id)
        )
    """)


def asegurar_columna_rol_en_usuario(cursor):
    """
    Agrega Usuario.Rol_Id si no existe todavia. Esta columna es una CACHE
    de solo lectura visual (la fuente de verdad sigue siendo Usuario_Rol);
    se actualiza con sincronizar_rol_id_usuario() cada vez que cambian los
    roles de un usuario especifico.
    """
    columnas = {fila[1] for fila in cursor.execute("PRAGMA table_info(Usuario)").fetchall()}
    if "Rol_Id" not in columnas:
        cursor.execute("ALTER TABLE Usuario ADD COLUMN Rol_Id INTEGER REFERENCES Rol(Rol_Id)")


def sincronizar_rol_id_usuario(cursor, usuario_id):
    """
    Recalcula Usuario.Rol_Id para UN usuario puntual, tomando el rol mas
    relevante (menor Rol_Id) de entre todos los que tenga en Usuario_Rol.
    Llamar siempre despues de insertar/eliminar filas en Usuario_Rol para
    ese usuario.
    """
    cursor.execute("""
        UPDATE Usuario
        SET Rol_Id = (
            SELECT MIN(UR.Rol_Id) FROM Usuario_Rol UR WHERE UR.Usuario_Id = ?
        )
        WHERE Usuario_Id = ?
    """, (usuario_id, usuario_id))


def listar_roles_catalogo():
    """Devuelve todos los roles disponibles (Rol_Id, Nombre_Rol), para llenar selects en el frontend."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT Rol_Id, Nombre_Rol FROM Rol ORDER BY Rol_Id")
        return [{"rol_id": fila[0], "nombre": fila[1]} for fila in cursor.fetchall()]
    finally:
        conexion.close()


def listar_usuarios_con_roles():
    """
    Devuelve todos los usuarios con su(s) rol(es) actual(es), para el panel
    de administracion de roles. Cada usuario incluye:
      - rol_id / rol_nombre: el rol mas relevante (columna cache de Usuario)
      - roles: lista completa de todos los roles que tiene en Usuario_Rol
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_usuario_rol(cursor)
        asegurar_columna_rol_en_usuario(cursor)
        conexion.commit()

        cursor.execute("""
            SELECT U.Usuario_Id, U.Nombre, U.Apellido, U.Correo, U.Estado, U.Rol_Id, R.Nombre_Rol
            FROM Usuario U
            LEFT JOIN Rol R ON U.Rol_Id = R.Rol_Id
            ORDER BY U.Usuario_Id
        """)
        filas_usuario = cursor.fetchall()

        cursor.execute("""
            SELECT UR.Usuario_Id, UR.Rol_Id, R.Nombre_Rol
            FROM Usuario_Rol UR
            JOIN Rol R ON UR.Rol_Id = R.Rol_Id
        """)
        roles_por_usuario = {}
        for usuario_id, rol_id, nombre_rol in cursor.fetchall():
            roles_por_usuario.setdefault(usuario_id, []).append({"rol_id": rol_id, "nombre": nombre_rol})

        usuarios = []
        for fila in filas_usuario:
            usuario_id = fila[0]
            usuarios.append({
                "usuario_id":  usuario_id,
                "nombre":      fila[1],
                "apellido":    fila[2],
                "correo":      fila[3] or "",
                "estado":      fila[4] or "",
                "rol_id":      fila[5],
                "rol_nombre":  fila[6] or "Sin rol",
                "roles":       sorted(roles_por_usuario.get(usuario_id, []), key=lambda r: r["rol_id"])
            })
        return usuarios
    finally:
        conexion.close()


def asignar_roles_usuario(usuario_id, roles_ids):
    """
    Reemplaza por completo el conjunto de roles de un usuario con los IDs
    dados (lista de enteros, ej. [1, 4] = Administrador + Cliente). Luego
    sincroniza la columna cache Usuario.Rol_Id. Si la lista queda vacia,
    el usuario se queda sin ningun rol (Usuario.Rol_Id pasa a NULL).
    """
    usuario_id = int(usuario_id)
    roles_unicos = sorted({int(r) for r in (roles_ids or [])})

    invalidos = [r for r in roles_unicos if r not in ROLES_VALIDOS]
    if invalidos:
        raise ValueError(f"Rol(es) invalido(s): {invalidos}")

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_usuario_rol(cursor)
        asegurar_columna_rol_en_usuario(cursor)

        cursor.execute("SELECT Usuario_Id FROM Usuario WHERE Usuario_Id = ?", (usuario_id,))
        if not cursor.fetchone():
            raise ValueError("El usuario no existe")

        cursor.execute("DELETE FROM Usuario_Rol WHERE Usuario_Id = ?", (usuario_id,))
        cursor.executemany(
            "INSERT OR IGNORE INTO Usuario_Rol (Usuario_Id, Rol_Id) VALUES (?, ?)",
            [(usuario_id, rol_id) for rol_id in roles_unicos]
        )
        sincronizar_rol_id_usuario(cursor, usuario_id)
        conexion.commit()

        cursor.execute("SELECT Rol_Id FROM Usuario WHERE Usuario_Id = ?", (usuario_id,))
        rol_resultante = cursor.fetchone()
        return {
            "usuario_id": usuario_id,
            "roles": roles_unicos,
            "rol_id": rol_resultante[0] if rol_resultante else None
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_usuarios():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT *
    FROM Usuario
    """)

    datos = cursor.fetchall()
    conexion.close()
    return datos


def asegurar_columnas_registro(cursor):
    """Agrega los campos del formulario web si la tabla Usuario aun no los tiene."""
    columnas = {fila[1] for fila in cursor.execute("PRAGMA table_info(Usuario)").fetchall()}
    nuevas_columnas = {
        "Correo": "TEXT",
        "Telefono": "TEXT",
        "Ciudad": "TEXT"
    }

    for columna, tipo in nuevas_columnas.items():
        if columna not in columnas:
            cursor.execute(f"ALTER TABLE Usuario ADD COLUMN {columna} {tipo}")

def validar_login(correo, contrasena):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT U.Usuario_Id, U.Nombre, U.Apellido, U.Estado, UR.Rol_Id,
                   U.Correo, U.Cedula,
                   COALESCE(T.Telefono, U.Telefono) AS Telefono
            FROM Usuario U
            LEFT JOIN Usuario_Rol UR ON U.Usuario_Id = UR.Usuario_Id
            LEFT JOIN Telefono T ON U.Usuario_Id = T.Usuario_Id
            WHERE U.Correo = ? AND U.Contrasena = ?
            ORDER BY CASE WHEN UR.Rol_Id IS NULL THEN 1 ELSE 0 END, UR.Rol_Id ASC
            LIMIT 1
        """, (correo, contrasena))

        usuario = cursor.fetchone()

        if usuario:
            rol_id = usuario[4]
            return {
                "id":       usuario[0],
                "nombre":   usuario[1],
                "apellido": usuario[2],
                "estado":   usuario[3],
                "rol_id":   rol_id,
                "es_admin": bool(rol_id and rol_id in (1, 2, 3)),
                "correo":   usuario[5],
                "cedula":   str(usuario[6]) if usuario[6] else "",
                "telefono": str(usuario[7]) if usuario[7] else ""
            }
        return None
    finally:
        conexion.close()


ROL_CLIENTE_ID = 4


def obtener_o_crear_pais(cursor, nombre_pais):
    pais = (nombre_pais or "").strip()
    if not pais:
        return None

    cursor.execute("SELECT Pais_Id FROM Pais WHERE LOWER(Nombre_Pais) = LOWER(?)", (pais,))
    existente = cursor.fetchone()
    if existente:
        return existente[0]

    cursor.execute("INSERT INTO Pais (Nombre_Pais) VALUES (?)", (pais,))
    return cursor.lastrowid

def actualizar_usuario(cursor, usuario_id, nombre, apellido, correo, telefono, ciudad):
    """
    Actualiza los datos de un usuario en la base de datos.
    """
    cursor.execute("""
        UPDATE Usuario
        SET Nombre = ?, Apellido = ?, Correo = ?, Telefono = ?, Ciudad = ?
        WHERE Usuario_Id = ?
    """, (nombre, apellido, correo, telefono, ciudad, usuario_id))
    
    return cursor.rowcount > 0


def crear_usuario(datos):
    nombre     = (datos.get("nombre")     or "").strip()
    apellido   = (datos.get("apellido")   or "").strip()
    correo     = (datos.get("correo")     or "").strip()
    cedula     = (datos.get("cedula")     or "").strip()
    telefono   = (datos.get("telefono")   or "").strip()
    pais       = (datos.get("pais")       or "").strip()
    ciudad     = (datos.get("ciudad")     or "").strip()
    contrasena = (datos.get("contrasena") or "").strip()

    if not all([nombre, apellido, correo, cedula, telefono, pais, ciudad, contrasena]):
        raise ValueError("Todos los campos del registro son obligatorios")

    digitos_cedula = "".join(c for c in cedula if c.isdigit())
    if not digitos_cedula:
        raise ValueError("El número de documento no es válido")
    cedula_int = int(digitos_cedula[:15])

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        asegurar_columnas_registro(cursor)
        asegurar_tabla_usuario_rol(cursor)
        asegurar_columna_rol_en_usuario(cursor)

        cursor.execute("SELECT Usuario_Id FROM Usuario WHERE LOWER(Correo) = LOWER(?)", (correo,))
        if cursor.fetchone():
            raise ValueError("El correo ya está registrado")

        cursor.execute("SELECT Usuario_Id FROM Usuario WHERE Telefono = ?", (telefono,))
        if cursor.fetchone():
            raise ValueError("El número de teléfono ya está registrado")

        cursor.execute("SELECT Usuario_Id FROM Usuario WHERE Cedula = ?", (cedula_int,))
        if cursor.fetchone():
            raise ValueError("El número de documento ya está registrado")

        pais_id = obtener_o_crear_pais(cursor, pais)

        cursor.execute("""
            INSERT INTO Usuario
                (Cedula, Nombre, Apellido, Estado, Contrasena, Pais_Id, Correo, Telefono, Ciudad)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cedula_int, nombre, apellido, "Activo", contrasena, pais_id, correo, telefono, ciudad))

        usuario_id = cursor.lastrowid

        cursor.execute(
            "INSERT OR IGNORE INTO Usuario_Rol (Usuario_Id, Rol_Id) VALUES (?, ?)",
            (usuario_id, ROL_CLIENTE_ID)
        )
        sincronizar_rol_id_usuario(cursor, usuario_id)

        conexion.commit()
        return {
            "usuario_id": usuario_id,
            "nombre":   nombre,
            "apellido": apellido,
            "correo":   correo,
            "cedula":   cedula_int,
            "telefono": telefono,
            "pais":     pais,
            "ciudad":   ciudad
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

