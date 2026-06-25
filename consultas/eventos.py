import sys
import os

# Asegurar que encuentre la carpeta 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar


def asegurar_columnas_eventos(cursor):
    columnas_evento = {fila[1] for fila in cursor.execute("PRAGMA table_info(Evento)").fetchall()}
    if "Imagen" not in columnas_evento:
        cursor.execute("ALTER TABLE Evento ADD COLUMN Imagen TEXT")

    columnas_funcion = {fila[1] for fila in cursor.execute("PRAGMA table_info(Funcion)").fetchall()}
    if "Ciudad" not in columnas_funcion:
        cursor.execute("ALTER TABLE Funcion ADD COLUMN Ciudad TEXT")


# 1. LISTAR EVENTOS
def listar_eventos():
    """Trae la lista basica de todos los eventos programados."""
    conexion = conectar()
    cursor = conexion.cursor()
    asegurar_columnas_eventos(cursor)
    conexion.commit()

    cursor.execute("""
        SELECT E.Evento_Id, E.Nombre, E.Fecha, E.Descripcion, E.Hora, U.Nombre, E.Imagen
        FROM Evento E
        LEFT JOIN Ubicacion U ON E.Ubicacion_Id = U.Ubicacion_Id
    """)

    datos = cursor.fetchall()
    conexion.close()
    return datos


# 2. BUSCAR EVENTO
def buscar_evento(evento_id):
    """Busca un evento especifico por su ID."""
    conexion = conectar()
    cursor = conexion.cursor()
    asegurar_columnas_eventos(cursor)
    conexion.commit()

    cursor.execute("""
        SELECT E.Evento_Id, E.Nombre, E.Fecha, E.Descripcion, E.Hora, U.Nombre, E.Imagen
        FROM Evento E
        LEFT JOIN Ubicacion U ON E.Ubicacion_Id = U.Ubicacion_Id
        WHERE E.Evento_Id = ?
    """, (evento_id,))

    evento = cursor.fetchone()
    conexion.close()
    return evento


# 3. CREAR EVENTO
def crear_evento(evento_id, nombre, fecha):
    """Inserta un nuevo evento en la base de datos."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO Evento (Evento_Id, Nombre, Fecha)
            VALUES (?, ?, ?)
        """, (evento_id, nombre, fecha))
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al crear evento: {e}")
        return False
    finally:
        conexion.close()


# 3b. CREAR EVENTO COMPLETO (desde Booking con fechas, hora, lugar e imagen)
def crear_evento_completo(datos):
    """
    Crea un evento nuevo en SQLite con todas sus funciones/fechas.
    Recibe un dict con: nombre, descripcion, hora, lugar, imagen, agenda (lista de {fecha, hora, lugar}).
    Devuelve el evento recien creado como tupla (igual que buscar_evento).
    """
    nombre      = (datos.get("nombre")      or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    hora        = (datos.get("hora")        or "").strip()
    ubicacion   = (datos.get("lugar")       or datos.get("ubicacion") or "").strip()
    imagen      = (datos.get("imagen")      or "").strip()
    agenda      = datos.get("agenda") or []

    if not nombre:
        raise ValueError("El nombre del evento es obligatorio")

    primera_fecha = agenda[0].get("fecha") if agenda else datos.get("fecha", "")
    primera_hora  = agenda[0].get("hora")  if agenda else hora

    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        asegurar_columnas_eventos(cursor)
        ubicacion_id = obtener_o_crear_ubicacion(cursor, ubicacion)

        cursor.execute("""
            INSERT INTO Evento (Nombre, Fecha, Hora, Descripcion, Ubicacion_Id, Imagen)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, primera_fecha, primera_hora, descripcion, ubicacion_id, imagen))
        evento_id = cursor.lastrowid

        for item in agenda:
            fecha_item  = (item.get("fecha")  or "").strip()
            hora_item   = (item.get("hora")   or "").strip()
            ciudad_item = (item.get("lugar")  or item.get("ciudad") or ubicacion or "").strip()
            if not fecha_item or not hora_item:
                continue
            crear_funcion_para_evento(cursor, evento_id, fecha_item, hora_item, ciudad_item)

        conexion.commit()
        return buscar_evento(evento_id)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


# 4. ACTUALIZAR EVENTO
def actualizar_evento(evento_id, nuevo_nombre, nueva_fecha):
    """Modifica los datos basicos de un evento existente."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE Evento
            SET Nombre = ?, Fecha = ?
            WHERE Evento_Id = ?
        """, (nuevo_nombre, nueva_fecha, evento_id))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al actualizar evento: {e}")
        return False
    finally:
        conexion.close()


# 5. ELIMINAR EVENTO
def eliminar_evento(evento_id):
    """Elimina un evento por su ID."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM Evento WHERE Evento_Id = ?", (evento_id,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar evento: {e}")
        return False
    finally:
        conexion.close()


def obtener_o_crear_ubicacion(cursor, nombre_ubicacion):
    ubicacion = (nombre_ubicacion or "").strip()
    if not ubicacion:
        return None

    cursor.execute("SELECT Ubicacion_Id FROM Ubicacion WHERE LOWER(Nombre) = LOWER(?)", (ubicacion,))
    existente = cursor.fetchone()
    if existente:
        return existente[0]

    cursor.execute("INSERT INTO Ubicacion (Nombre) VALUES (?)", (ubicacion,))
    return cursor.lastrowid


def obtener_funciones_evento(cursor, evento_id):
    cursor.execute("""
        SELECT DISTINCT F.Funcion_Id
        FROM Evento_Boleta EB
        JOIN Boleta B ON EB.Boleta_Id = B.Boleta_Id
        JOIN Funcion_Localidad FL ON B.Funcion_Localidad_Id = FL.Funcion_Localidad_Id
        JOIN Funcion F ON FL.Funcion_Id = F.Funcion_Id
        WHERE EB.Evento_Id = ?
        ORDER BY F.Funcion_Id
    """, (evento_id,))
    return [fila[0] for fila in cursor.fetchall()]


def obtener_localidad_default(cursor):
    cursor.execute("SELECT Localidad_Id FROM Localidad ORDER BY Localidad_Id LIMIT 1")
    localidad = cursor.fetchone()
    if localidad:
        return localidad[0]
    cursor.execute("INSERT INTO Localidad (Nombre) VALUES ('General')")
    return cursor.lastrowid


def obtener_precio_stock_default(cursor, evento_id):
    cursor.execute("""
        SELECT FL.Precio, FL.Stock
        FROM Evento_Boleta EB
        JOIN Boleta B ON EB.Boleta_Id = B.Boleta_Id
        JOIN Funcion_Localidad FL ON B.Funcion_Localidad_Id = FL.Funcion_Localidad_Id
        WHERE EB.Evento_Id = ?
        LIMIT 1
    """, (evento_id,))
    datos = cursor.fetchone()
    if datos:
        return datos[0] or 0, datos[1] or 100
    return 0, 100


def crear_funcion_para_evento(cursor, evento_id, fecha, hora, ciudad):
    cursor.execute("INSERT INTO Funcion (Fecha, Hora, Ciudad) VALUES (?, ?, ?)", (fecha, hora, ciudad))
    funcion_id = cursor.lastrowid
    localidad_id = obtener_localidad_default(cursor)
    precio, stock = obtener_precio_stock_default(cursor, evento_id)

    cursor.execute("""
        INSERT INTO Funcion_Localidad (Funcion_Id, Localidad_Id, Precio, Stock)
        VALUES (?, ?, ?, ?)
    """, (funcion_id, localidad_id, precio, stock))
    funcion_localidad_id = cursor.lastrowid

    cursor.execute("INSERT INTO Boleta (Funcion_Localidad_Id) VALUES (?)", (funcion_localidad_id,))
    boleta_id = cursor.lastrowid

    cursor.execute("INSERT OR IGNORE INTO Evento_Boleta (Evento_Id, Boleta_Id) VALUES (?, ?)", (evento_id, boleta_id))
    return funcion_id


def actualizar_evento_desde_booking(evento_id, datos):
    """Actualiza un evento SQLite desde Booking sin cambiar el flujo del frontend."""
    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    ubicacion = (datos.get("lugar") or datos.get("ubicacion") or "").strip()
    hora = (datos.get("hora") or "").strip()
    imagen = (datos.get("imagen") or "").strip()
    agenda = datos.get("agenda") or []

    if not nombre:
        raise ValueError("El nombre del evento es obligatorio")

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        asegurar_columnas_eventos(cursor)
        ubicacion_id = obtener_o_crear_ubicacion(cursor, ubicacion)
        primera_fecha = agenda[0].get("fecha") if agenda else datos.get("fecha")
        primera_hora = agenda[0].get("hora") if agenda else hora

        cursor.execute("""
            UPDATE Evento
            SET Nombre = ?, Fecha = ?, Hora = ?, Descripcion = ?, Ubicacion_Id = ?, Imagen = ?
            WHERE Evento_Id = ?
        """, (nombre, primera_fecha, primera_hora, descripcion, ubicacion_id, imagen, evento_id))

        if cursor.rowcount == 0:
            raise ValueError("El evento no existe en SQLite")

        funciones = obtener_funciones_evento(cursor, evento_id)
        for indice, item in enumerate(agenda):
            fecha_item = (item.get("fecha") or "").strip()
            hora_item = (item.get("hora") or "").strip()
            ciudad_item = (item.get("lugar") or item.get("ciudad") or ubicacion or "").strip()
            if not fecha_item or not hora_item:
                continue

            if indice < len(funciones):
                cursor.execute("""
                    UPDATE Funcion
                    SET Fecha = ?, Hora = ?, Ciudad = ?
                    WHERE Funcion_Id = ?
                """, (fecha_item, hora_item, ciudad_item, funciones[indice]))
            else:
                crear_funcion_para_evento(cursor, evento_id, fecha_item, hora_item, ciudad_item)

        conexion.commit()
        return buscar_evento(evento_id)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


# 6. CONSULTAR AFORO
def consultar_aforo():
    """
    Une las funciones y localidades para saber el stock total
    de boletas planeadas/disponibles por cada evento en el sistema.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    asegurar_columnas_eventos(cursor)
    conexion.commit()

    cursor.execute("""
        SELECT E.Nombre, F.Fecha, F.Hora, SUM(FL.Stock) as Aforo_Total,
               COALESCE(F.Ciudad, U.Nombre) as Lugar
        FROM Evento E
        LEFT JOIN Ubicacion U ON E.Ubicacion_Id = U.Ubicacion_Id
        JOIN Evento_Boleta EB ON E.Evento_Id = EB.Evento_Id
        JOIN Boleta B ON EB.Boleta_Id = B.Boleta_Id
        JOIN Funcion_Localidad FL ON B.Funcion_Localidad_Id = FL.Funcion_Localidad_Id
        JOIN Funcion F ON FL.Funcion_Id = F.Funcion_Id
        GROUP BY E.Evento_Id, F.Funcion_Id
        ORDER BY E.Evento_Id, F.Funcion_Id
    """)

    datos = cursor.fetchall()
    conexion.close()
    return datos