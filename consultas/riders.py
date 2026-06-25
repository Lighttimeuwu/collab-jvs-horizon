import sys
import os
from datetime import datetime

# Asegurar que encuentre la carpeta 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar


def asegurar_tabla_riders(cursor):
    """
    Crea la tabla Rider_Archivo si no existe. No toca ninguna tabla existente
    (Rider_Tecnico / Artista_Rider quedan intactas).

    Artista_Id_Frontend guarda el identificador que ya usa el frontend
    (ej. 'art1', 'art2', 'sqlite_7'...), para no depender de que cada
    artista tenga fila propia en la tabla Artista.
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Rider_Archivo (
            Rider_Archivo_Id   INTEGER PRIMARY KEY AUTOINCREMENT,
            Artista_Id_Frontend TEXT NOT NULL UNIQUE,
            Nombre_Archivo      TEXT NOT NULL,
            Tipo_Archivo        TEXT NOT NULL DEFAULT '',
            Contenido_Base64    TEXT NOT NULL,
            Fecha_Subida        TEXT NOT NULL
        )
    """)


def guardar_rider(artista_id, nombre_archivo, tipo_archivo, contenido_base64):
    """Guarda o reemplaza el rider tecnico vinculado a un artista/evento."""
    artista_id = (artista_id or "").strip()
    nombre_archivo = (nombre_archivo or "").strip()
    contenido_base64 = contenido_base64 or ""

    if not artista_id:
        raise ValueError("Falta el identificador del artista/evento")
    if not nombre_archivo:
        raise ValueError("Falta el nombre del archivo")
    if not contenido_base64:
        raise ValueError("Falta el contenido del archivo")

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_riders(cursor)
        fecha_subida = datetime.now().isoformat(timespec="seconds")

        cursor.execute("""
            INSERT INTO Rider_Archivo
                (Artista_Id_Frontend, Nombre_Archivo, Tipo_Archivo, Contenido_Base64, Fecha_Subida)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(Artista_Id_Frontend) DO UPDATE SET
                Nombre_Archivo   = excluded.Nombre_Archivo,
                Tipo_Archivo     = excluded.Tipo_Archivo,
                Contenido_Base64 = excluded.Contenido_Base64,
                Fecha_Subida     = excluded.Fecha_Subida
        """, (artista_id, nombre_archivo, tipo_archivo, contenido_base64, fecha_subida))

        conexion.commit()
        return {
            "artista_id": artista_id,
            "nombre_archivo": nombre_archivo,
            "tipo_archivo": tipo_archivo,
            "fecha_subida": fecha_subida
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def obtener_rider(artista_id):
    """Devuelve el rider tecnico (con su contenido) de un artista/evento, o None."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_riders(cursor)
        cursor.execute("""
            SELECT Artista_Id_Frontend, Nombre_Archivo, Tipo_Archivo, Contenido_Base64, Fecha_Subida
            FROM Rider_Archivo
            WHERE Artista_Id_Frontend = ?
        """, (artista_id,))

        fila = cursor.fetchone()
        if not fila:
            return None

        return {
            "artista_id": fila[0],
            "nombre_archivo": fila[1],
            "tipo_archivo": fila[2],
            "contenido_base64": fila[3],
            "fecha_subida": fila[4]
        }
    finally:
        conexion.close()


def listar_riders():
    """Devuelve, sin el contenido pesado, el estado de los riders de todos los artistas/eventos."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_riders(cursor)
        cursor.execute("""
            SELECT Artista_Id_Frontend, Nombre_Archivo, Tipo_Archivo, Fecha_Subida
            FROM Rider_Archivo
        """)

        return [
            {
                "artista_id": fila[0],
                "nombre_archivo": fila[1],
                "tipo_archivo": fila[2],
                "fecha_subida": fila[3]
            }
            for fila in cursor.fetchall()
        ]
    finally:
        conexion.close()


def eliminar_rider(artista_id):
    """Elimina el rider tecnico vinculado a un artista/evento. Devuelve True si elimino algo."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_riders(cursor)
        cursor.execute("DELETE FROM Rider_Archivo WHERE Artista_Id_Frontend = ?", (artista_id,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()