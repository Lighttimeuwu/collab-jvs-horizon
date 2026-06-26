import sys
import os

# Agregamos la carpeta raiz al sistema para que encuentre 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

# Ahora el import funcionara siempre, uses o no el boton de Play de VS Code
from utilidades.conexion import conectar


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
        # Traemos también Cedula y Telefono para autocompletar la pasarela PSE
        cursor.execute("""
            SELECT U.Usuario_Id, U.Nombre, U.Apellido, U.Estado, AR.Rol_Id,
                   U.Correo, U.Cedula,
                   COALESCE(T.Telefono, U.Telefono) AS Telefono
            FROM Usuario U
            LEFT JOIN Administrador_Rol AR ON U.Usuario_Id = AR.Administrador_Id
            LEFT JOIN Telefono T ON U.Usuario_Id = T.Usuario_Id
            WHERE U.Correo = ? AND U.Contrasena = ?
            LIMIT 1
        """, (correo, contrasena))

        usuario = cursor.fetchone()

        if usuario:
            return {
                "id":       usuario[0],
                "nombre":   usuario[1],
                "apellido": usuario[2],
                "estado":   usuario[3],
                "es_admin": bool(usuario[4]),
                "correo":   usuario[5],
                "cedula":   str(usuario[6]) if usuario[6] else "",
                "telefono": str(usuario[7]) if usuario[7] else ""
            }
        return None
    finally:
        conexion.close()


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


def crear_usuario(datos):
    nombre = (datos.get("nombre") or "").strip()
    apellido = (datos.get("apellido") or "").strip()
    correo = (datos.get("correo") or "").strip()
    telefono = (datos.get("telefono") or "").strip()
    pais = (datos.get("pais") or "").strip()
    ciudad = (datos.get("ciudad") or "").strip()
    contrasena = (datos.get("contrasena") or "").strip()

    if not all([nombre, apellido, correo, telefono, pais, ciudad, contrasena]):
        raise ValueError("Todos los campos del registro son obligatorios")

    digitos_telefono = "".join(caracter for caracter in telefono if caracter.isdigit())
    cedula_temporal = int(digitos_telefono[-10:] or "0")

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        asegurar_columnas_registro(cursor)
        pais_id = obtener_o_crear_pais(cursor, pais)

        cursor.execute("""
            INSERT INTO Usuario
                (Cedula, Nombre, Apellido, Estado, Contrasena, Pais_Id, Correo, Telefono, Ciudad)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cedula_temporal,
            nombre,
            apellido,
            "Activo",
            contrasena,
            pais_id,
            correo,
            telefono,
            ciudad
        ))

        conexion.commit()
        return {
            "usuario_id": cursor.lastrowid,
            "nombre": nombre,
            "apellido": apellido,
            "correo": correo,
            "telefono": telefono,
            "pais": pais,
            "ciudad": ciudad
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()