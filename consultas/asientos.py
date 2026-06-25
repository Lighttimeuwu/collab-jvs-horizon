import hashlib
import os
import sys
from datetime import datetime

ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar


def generar_funcion_id(evento_nombre, fecha_evento):
    """
    Genera un identificador numerico estable a partir de evento+fecha.

    La tabla Asiento_Ocupado tiene una restriccion UNIQUE(Evento_Id, Funcion_Id, Asiento).
    Como el codigo anterior siempre guardaba Evento_Id=0 y Funcion_Id=0, el mismo
    codigo de asiento (ej. "vip-A1") quedaba "ocupado" para TODOS los eventos a la vez,
    por eso las sillas se entrecruzaban entre distintos artistas/fechas.
    Generamos un numero unico por combinacion evento+fecha para que cada
    evento/fecha tenga su propio espacio de asientos dentro de esa restriccion.
    """
    clave = f"{evento_nombre.strip().lower()}|{fecha_evento.strip().lower()}"
    digesto = hashlib.sha1(clave.encode("utf-8")).hexdigest()
    # Tomamos los primeros 12 caracteres hex (48 bits) para evitar overflow de INTEGER en SQLite.
    return int(digesto[:12], 16)


def asegurar_tabla_asientos(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Asiento_Ocupado (
            Asiento_Ocupado_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Evento_Id INTEGER NOT NULL DEFAULT 0,
            Funcion_Id INTEGER NOT NULL DEFAULT 0,
            Asiento TEXT NOT NULL,
            Estado TEXT NOT NULL DEFAULT 'Ocupado',
            Fecha_Compra TEXT NOT NULL,
            Evento_Nombre TEXT NOT NULL DEFAULT '',
            Fecha_Evento TEXT NOT NULL DEFAULT ''
        )
    """)


def consultar_asientos_ocupados(datos):
    """Consulta asientos ocupados por nombre de evento y fecha."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_asientos(cursor)

        evento_nombre = (datos.get("evento") or "").strip()
        fecha_evento  = (datos.get("fecha")  or "").strip()

        if not evento_nombre or not fecha_evento:
            return {"asientos": [], "evento": evento_nombre, "fecha": fecha_evento}

        cursor.execute("""
            SELECT Asiento
            FROM Asiento_Ocupado
            WHERE LOWER(Evento_Nombre) = LOWER(?)
              AND LOWER(Fecha_Evento)  = LOWER(?)
              AND Estado = 'Ocupado'
            ORDER BY Asiento
        """, (evento_nombre, fecha_evento))

        asientos = [fila[0] for fila in cursor.fetchall()]
        return {
            "asientos": asientos,
            "evento": evento_nombre,
            "fecha": fecha_evento
        }
    finally:
        conexion.close()


def registrar_asientos_ocupados(datos):
    """Registra asientos comprados usando nombre de evento y fecha como clave."""
    asientos = datos.get("asientos") or []
    if not isinstance(asientos, list) or len(asientos) == 0:
        raise ValueError("Debe enviar al menos un asiento")

    evento_nombre = (datos.get("evento") or "").strip()
    fecha_evento  = (datos.get("fecha")  or "").strip()

    if not evento_nombre:
        raise ValueError("Falta el nombre del evento")
    if not fecha_evento:
        raise ValueError("Falta la fecha del evento")

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_asientos(cursor)

        fecha_compra = datetime.now().isoformat(timespec="seconds")
        funcion_id = generar_funcion_id(evento_nombre, fecha_evento)

        for asiento in asientos:
            cursor.execute("""
                SELECT Asiento_Ocupado_Id FROM Asiento_Ocupado
                WHERE LOWER(Evento_Nombre) = LOWER(?)
                  AND LOWER(Fecha_Evento)  = LOWER(?)
                  AND Asiento = ?
            """, (evento_nombre, fecha_evento, str(asiento)))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO Asiento_Ocupado
                        (Evento_Id, Funcion_Id, Asiento, Estado, Fecha_Compra, Evento_Nombre, Fecha_Evento)
                    VALUES (0, ?, ?, 'Ocupado', ?, ?, ?)
                """, (funcion_id, str(asiento), fecha_compra, evento_nombre, fecha_evento))

        conexion.commit()

        cursor.execute("""
            SELECT Asiento FROM Asiento_Ocupado
            WHERE LOWER(Evento_Nombre) = LOWER(?)
              AND LOWER(Fecha_Evento)  = LOWER(?)
              AND Estado = 'Ocupado'
            ORDER BY Asiento
        """, (evento_nombre, fecha_evento))

        asientos_totales = [fila[0] for fila in cursor.fetchall()]
        return {
            "asientos": asientos_totales,
            "evento": evento_nombre,
            "fecha": fecha_evento
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()