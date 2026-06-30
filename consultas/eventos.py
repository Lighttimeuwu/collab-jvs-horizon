import sys
import os

# Asegurar que encuentre la carpeta 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar
from consultas.riders import asegurar_tabla_riders


def asegurar_columnas_eventos(cursor):
    columnas_evento = {fila[1] for fila in cursor.execute("PRAGMA table_info(Evento)").fetchall()}
    if "Imagen" not in columnas_evento:
        cursor.execute("ALTER TABLE Evento ADD COLUMN Imagen TEXT")
    if "Publicado" not in columnas_evento:
        cursor.execute("ALTER TABLE Evento ADD COLUMN Publicado INTEGER NOT NULL DEFAULT 0")

    columnas_funcion = {fila[1] for fila in cursor.execute("PRAGMA table_info(Funcion)").fetchall()}
    if "Ciudad" not in columnas_funcion:
        cursor.execute("ALTER TABLE Funcion ADD COLUMN Ciudad TEXT")


def asegurar_tabla_personal_tecnico(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Personal_Tecnico_Evento (
            Personal_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Evento_Id   INTEGER NOT NULL,
            Nombre      TEXT NOT NULL,
            Funciones   TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (Evento_Id) REFERENCES Evento(Evento_Id)
        )
    """)


# 1. LISTAR EVENTOS
def listar_eventos(ciudad=None):
    """Trae la lista basica de todos los eventos programados, permitiendo filtrar por ciudad."""
    conexion = conectar()
    cursor = conexion.cursor()
    asegurar_columnas_eventos(cursor)
    conexion.commit()

    # ✅ FIX: La query completa se escribe en ambas ramas.
    # El patrón de ciudad NO usa paréntesis para ser compatible con
    # ubicaciones antiguas ("Movistar Arena") y nuevas ("Movistar Arena (Bogotá)").
    if ciudad:
        patron_busqueda = f"%{ciudad}%"
        cursor.execute("""
            SELECT E.Evento_Id, E.Nombre, E.Fecha, E.Descripcion, E.Hora, U.Nombre, E.Imagen, E.Publicado
            FROM Evento E
            LEFT JOIN Ubicacion U ON E.Ubicacion_Id = U.Ubicacion_Id
            WHERE U.Nombre LIKE ?
        """, (patron_busqueda,))
    else:
        cursor.execute("""
            SELECT E.Evento_Id, E.Nombre, E.Fecha, E.Descripcion, E.Hora, U.Nombre, E.Imagen, E.Publicado
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
        SELECT E.Evento_Id, E.Nombre, E.Fecha, E.Descripcion, E.Hora, U.Nombre, E.Imagen, E.Publicado
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
    """
    Elimina un evento por su ID, junto con TODO lo que depende de el.

    Tablas que referencian a Evento/Boleta/Funcion_Localidad/Funcion
    (confirmadas con PRAGMA foreign_key_list sobre el esquema real):
      - Evento_Artista       (Evento_Id -> Evento)
      - Evento_Producto      (Evento_Id -> Evento)
      - Evento_Proveedor     (Evento_Id -> Evento)
      - Evento_Coordinador   (Evento_Id -> Evento)
      - Personal_Tecnico_Evento (Evento_Id -> Evento)
      - Evento_Boleta        (Evento_Id -> Evento, Boleta_Id -> Boleta)
      - Detalle_Pago         (Funcion_Localidad_Id -> Funcion_Localidad)
      - Boleta               (Funcion_Localidad_Id -> Funcion_Localidad)
      - Funcion_Localidad    (Funcion_Id -> Funcion)
      - Asiento_Ocupado      (sin FK declarada, pero referencia logica a Evento_Id)
      - Rider_Archivo        (via 'sqlite_<Evento_Id>' como Artista_Id_Frontend)

    Las filas de Boleta/Funcion_Localidad/Funcion/Detalle_Pago se ubican
    siempre a traves de Evento_Boleta (la tabla puente de ESTE evento), por
    lo que nunca se tocan funciones, boletas o pagos de otro evento.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_personal_tecnico(cursor)

        # 1) Ubicar Boletas / Funcion_Localidad / Funcion que pertenecen a ESTE evento
        cursor.execute("SELECT Boleta_Id FROM Evento_Boleta WHERE Evento_Id = ?", (evento_id,))
        boleta_ids = [fila[0] for fila in cursor.fetchall()]

        funcion_localidad_ids = []
        funcion_ids = []
        if boleta_ids:
            placeholders = ",".join("?" * len(boleta_ids))
            cursor.execute(
                f"SELECT DISTINCT Funcion_Localidad_Id FROM Boleta WHERE Boleta_Id IN ({placeholders})",
                boleta_ids
            )
            funcion_localidad_ids = [fila[0] for fila in cursor.fetchall() if fila[0] is not None]

        if funcion_localidad_ids:
            placeholders_fl = ",".join("?" * len(funcion_localidad_ids))
            cursor.execute(
                f"SELECT DISTINCT Funcion_Id FROM Funcion_Localidad WHERE Funcion_Localidad_Id IN ({placeholders_fl})",
                funcion_localidad_ids
            )
            funcion_ids = [fila[0] for fila in cursor.fetchall() if fila[0] is not None]

        # 2) Borrar TODO lo que cuelga de las Funcion_Localidad de este evento,
        #    empezando por Detalle_Pago (pagos/ventas ya registrados)
        if funcion_localidad_ids:
            placeholders_fl = ",".join("?" * len(funcion_localidad_ids))
            cursor.execute(
                f"DELETE FROM Detalle_Pago WHERE Funcion_Localidad_Id IN ({placeholders_fl})",
                funcion_localidad_ids
            )

        # 3) Evento_Boleta -> Boleta -> Funcion_Localidad -> Funcion
        cursor.execute("DELETE FROM Evento_Boleta WHERE Evento_Id = ?", (evento_id,))

        if boleta_ids:
            placeholders = ",".join("?" * len(boleta_ids))
            cursor.execute(f"DELETE FROM Boleta WHERE Boleta_Id IN ({placeholders})", boleta_ids)

        if funcion_localidad_ids:
            placeholders_fl = ",".join("?" * len(funcion_localidad_ids))
            cursor.execute(
                f"DELETE FROM Funcion_Localidad WHERE Funcion_Localidad_Id IN ({placeholders_fl})",
                funcion_localidad_ids
            )

        if funcion_ids:
            placeholders_f = ",".join("?" * len(funcion_ids))
            cursor.execute(f"DELETE FROM Funcion WHERE Funcion_Id IN ({placeholders_f})", funcion_ids)

        # 4) Todas las tablas puente que referencian directamente a Evento_Id
        cursor.execute("DELETE FROM Evento_Artista WHERE Evento_Id = ?", (evento_id,))
        cursor.execute("DELETE FROM Evento_Producto WHERE Evento_Id = ?", (evento_id,))
        cursor.execute("DELETE FROM Evento_Proveedor WHERE Evento_Id = ?", (evento_id,))
        cursor.execute("DELETE FROM Evento_Coordinador WHERE Evento_Id = ?", (evento_id,))
        cursor.execute("DELETE FROM Personal_Tecnico_Evento WHERE Evento_Id = ?", (evento_id,))

        # 5) Asientos ocupados ligados a este evento (no tiene FK declarada,
        #    pero igual queda huerfana si no se limpia)
        cursor.execute("DELETE FROM Asiento_Ocupado WHERE Evento_Id = ?", (evento_id,))

        # 6) Rider tecnico vinculado. El frontend identifica los riders de
        #    eventos guardados en SQLite con el id 'sqlite_<Evento_Id>'
        #    (ver script.js: id: 'sqlite_' + evento.id), por eso se borra
        #    usando esa misma clave compuesta.
        asegurar_tabla_riders(cursor)
        cursor.execute(
            "DELETE FROM Rider_Archivo WHERE Artista_Id_Frontend = ?",
            (f"sqlite_{evento_id}",)
        )

        # 7) Por ultimo, el evento en si
        cursor.execute("DELETE FROM Evento WHERE Evento_Id = ?", (evento_id,))

        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conexion.rollback()
        print(f"Error al eliminar evento: {e}")
        return False
    finally:
        conexion.close()


def obtener_o_crear_ubicacion(cursor, nombre_ubicacion):
    ubicacion = (nombre_ubicacion or "").strip()
    if not ubicacion:
        return None

    # ✅ FIX: Normaliza "Movistar Arena (Bogotá)" → "Movistar Arena"
    # para que haga match con los nombres existentes en la tabla Ubicacion.
    nombre_normalizado = ubicacion.split("(")[0].strip()

    cursor.execute(
        "SELECT Ubicacion_Id FROM Ubicacion WHERE LOWER(Nombre) = LOWER(?)",
        (nombre_normalizado,)
    )
    existente = cursor.fetchone()
    if existente:
        return existente[0]

    cursor.execute("INSERT INTO Ubicacion (Nombre) VALUES (?)", (nombre_normalizado,))
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
    """Actualiza un evento SQLite desde Booking y sincroniza las facturas viejas."""
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
        
        # 1. Obtener el nombre antiguo del evento antes de modificarlo
        # (Lo necesitamos porque la tabla Ventas_Web busca los eventos por su nombre)
        cursor.execute("SELECT Nombre FROM Evento WHERE Evento_Id = ?", (evento_id,))
        fila_antigua = cursor.fetchone()
        if not fila_antigua:
            raise ValueError("El evento no existe en SQLite")
        nombre_antiguo = fila_antigua[0]

        ubicacion_id = obtener_o_crear_ubicacion(cursor, ubicacion)
        primera_fecha = agenda[0].get("fecha") if agenda else datos.get("fecha")
        primera_hora = agenda[0].get("hora") if agenda else hora

        # 2. Actualizar el evento
        cursor.execute("""
            UPDATE Evento
            SET Nombre = ?, Fecha = ?, Hora = ?, Descripcion = ?, Ubicacion_Id = ?, Imagen = ?
            WHERE Evento_Id = ?
        """, (nombre, primera_fecha, primera_hora, descripcion, ubicacion_id, imagen, evento_id))

        # 3. ACTUALIZAR LAS FACTURAS VIEJAS (Mis Entradas)
        cursor.execute("""
            UPDATE Ventas_Web
            SET Evento = ?, Fecha_Evento = ?, Lugar = ?
            WHERE Evento = ?
        """, (nombre, primera_fecha, ubicacion, nombre_antiguo))

        # 4. Actualizar las funciones
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
        SELECT E.Evento_Id, E.Nombre, F.Fecha, F.Hora, SUM(FL.Stock) as Aforo_Total,
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


# ─── Publicación a cartelera (visible para usuarios finales) ──────────────

def publicar_evento(evento_id):
    """Marca un evento como publicado (visible en la cartelera de usuarios)."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_columnas_eventos(cursor)
        cursor.execute("UPDATE Evento SET Publicado = 1 WHERE Evento_Id = ?", (evento_id,))
        if cursor.rowcount == 0:
            raise ValueError("El evento no existe")
        conexion.commit()
        return buscar_evento(evento_id)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def despublicar_evento(evento_id):
    """Retira un evento de la cartelera publica (vuelve a quedar oculto)."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_columnas_eventos(cursor)
        cursor.execute("UPDATE Evento SET Publicado = 0 WHERE Evento_Id = ?", (evento_id,))
        if cursor.rowcount == 0:
            raise ValueError("El evento no existe")
        conexion.commit()
        return buscar_evento(evento_id)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


# ─── Personal técnico asignado a un evento ─────────────────────────────────

def listar_personal_tecnico(evento_id):
    """Devuelve el personal tecnico asignado a un evento."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_personal_tecnico(cursor)
        cursor.execute("""
            SELECT Personal_Id, Nombre, Funciones
            FROM Personal_Tecnico_Evento
            WHERE Evento_Id = ?
            ORDER BY Personal_Id
        """, (evento_id,))
        return [
            {
                "personal_id": fila[0],
                "nombre": fila[1],
                "funciones": fila[2].split("|") if fila[2] else []
            }
            for fila in cursor.fetchall()
        ]
    finally:
        conexion.close()


def agregar_personal_tecnico(evento_id, nombre, funciones):
    """Agrega una persona de personal tecnico a un evento."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre del personal es obligatorio")

    funciones_texto = "|".join(f.strip() for f in (funciones or []) if f.strip())

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_personal_tecnico(cursor)
        cursor.execute("""
            INSERT INTO Personal_Tecnico_Evento (Evento_Id, Nombre, Funciones)
            VALUES (?, ?, ?)
        """, (evento_id, nombre, funciones_texto))
        conexion.commit()
        return {"personal_id": cursor.lastrowid, "nombre": nombre, "funciones": funciones or []}
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def eliminar_personal_tecnico(personal_id):
    """Elimina una persona de personal tecnico por su Personal_Id."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_tabla_personal_tecnico(cursor)
        cursor.execute("DELETE FROM Personal_Tecnico_Evento WHERE Personal_Id = ?", (personal_id,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def guardar_imagen_evento(evento_id, imagen_base64):
    """
    Guarda o actualiza la imagen (base64 o URL) de un evento existente.
    Lanza ValueError si el evento no existe.
    """
    imagen = (imagen_base64 or "").strip()
    if not imagen:
        raise ValueError("La imagen no puede estar vacía")

    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        asegurar_columnas_eventos(cursor)
        cursor.execute("SELECT Evento_Id FROM Evento WHERE Evento_Id = ?", (evento_id,))
        if not cursor.fetchone():
            raise ValueError("El evento no existe")

        cursor.execute("UPDATE Evento SET Imagen = ? WHERE Evento_Id = ?", (imagen, evento_id))
        conexion.commit()
        return True
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def despublicar_eventos_vencidos():
    """
    Revisa todos los eventos publicados y despublica los que ya no tienen
    ninguna función futura (todas sus fechas pasaron o no tienen funciones).
    """
    from datetime import date
    hoy = date.today().isoformat()

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_columnas_eventos(cursor)

        cursor.execute("""
            SELECT DISTINCT E.Evento_Id
            FROM Evento E
            JOIN Funcion F ON F.Funcion_Id IN (
                SELECT FL.Funcion_Id FROM Funcion_Localidad FL
                JOIN Boleta B ON B.Funcion_Localidad_Id = FL.Funcion_Localidad_Id
                JOIN Evento_Boleta EB ON EB.Boleta_Id = B.Boleta_Id
                WHERE EB.Evento_Id = E.Evento_Id
            )
            WHERE E.Publicado = 1 AND F.Fecha >= ?
        """, (hoy,))
        con_fechas_vigentes = {fila[0] for fila in cursor.fetchall()}

        cursor.execute("SELECT Evento_Id FROM Evento WHERE Publicado = 1")
        todos_publicados = [fila[0] for fila in cursor.fetchall()]

        vencidos = [eid for eid in todos_publicados if eid not in con_fechas_vigentes]
        if vencidos:
            cursor.executemany(
                "UPDATE Evento SET Publicado = 0 WHERE Evento_Id = ?",
                [(eid,) for eid in vencidos]
            )
            conexion.commit()

        return vencidos
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()