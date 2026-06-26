import sys
import os
import hashlib

# Asegurar que encuentre la carpeta 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar

PRECIO_UNITARIO_DEFAULT = 85000


def registrar_venta(boleta_id, usuario_id, pasarela_id=1):
    """
    Registra la venta en Detalle_Pago asegurando previamente 
    que existan los IDs en las tablas padres para evitar el IntegrityError.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO Usuario (Usuario_Id, Nombre, Apellido, Correo, Contrasena) 
            VALUES (?, 'Usuario', 'Temporal', 'temp@correo.com', '123')
        """, (usuario_id,))
        
        cursor.execute("""
            INSERT OR IGNORE INTO Pasarela_Pago (Pasarela_Id, Nombre_Pasarela, Estado) 
            VALUES (?, 'Pasarela Global', 'Activo')
        """, (pasarela_id,))
        
        cursor.execute("""
            INSERT OR IGNORE INTO Boleta (Boleta_Id, Funcion_Localidad_Id, Codigo_Barras, Estado) 
            VALUES (?, 1, 'TEMP-CODE-123', 'Vendido')
        """, (boleta_id,))
        
        cursor.execute("""
            INSERT INTO Detalle_Pago 
            VALUES (NULL, ?, ?, ?)
        """, (boleta_id, usuario_id, pasarela_id))
        
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error interno en la transaccion de venta: {e}")
        return False
    finally:
        conexion.close()

def listar_historial_ventas():
    """
    Historial inteligente: Trae los datos de los compradores uniendo 
    las tablas de forma limpia y directa.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT U.Nombre || ' ' || U.Apellido as Cliente,
                   'Boleto ID: ' || DP.Boleta_Id as Item
            FROM Detalle_Pago DP
            JOIN Usuario U ON DP.Usuario_Id = U.Usuario_Id
        """)
        datos = cursor.fetchall()
        return datos
    except Exception as e:
        print(f"Error al consultar historial: {e}")
        return []
    finally:
        conexion.close()


# Funciones nuevas para el historial de entradas del usuario

def _asegurar_columnas_boleta(cursor):
    """Agrega Usuario_Id y Asiento a Boleta si no existen."""
    columnas = {fila[1] for fila in cursor.execute("PRAGMA table_info(Boleta)").fetchall()}
    if "Usuario_Id" not in columnas:
        cursor.execute("ALTER TABLE Boleta ADD COLUMN Usuario_Id INTEGER REFERENCES Usuario(Usuario_Id)")
    if "Asiento" not in columnas:
        cursor.execute("ALTER TABLE Boleta ADD COLUMN Asiento TEXT")


def _buscar_usuario_id(cursor, correo):
    """Devuelve el Usuario_Id a partir del correo. None si no existe."""
    if not correo:
        return None
    cursor.execute(
        "SELECT Usuario_Id FROM Usuario WHERE LOWER(Correo) = LOWER(?) LIMIT 1",
        (correo,)
    )
    fila = cursor.fetchone()
    return fila[0] if fila else None


def _generar_funcion_id_estable(evento_nombre, fecha_evento):
    """
    Mismo esquema que consultas/asientos.py: genera un Funcion_Id numerico
    estable a partir de evento+fecha, para que cada combinacion evento/fecha
    tenga su propia Funcion en la BD (y por lo tanto su propia
    Funcion_Localidad), en vez de reutilizar siempre Funcion_Localidad_Id=1.
    """
    clave = f"{evento_nombre.strip().lower()}|{fecha_evento.strip().lower()}"
    digesto = hashlib.sha1(clave.encode("utf-8")).hexdigest()
    return int(digesto[:12], 16)


def _obtener_o_crear_funcion_localidad(cursor, evento_nombre, fecha_evento, lugar):
    """
    Devuelve el Funcion_Localidad_Id real correspondiente al evento+fecha
    comprado, creando la Funcion y la Funcion_Localidad si todavia no existen.
    Esto evita el bug de guardar siempre Funcion_Localidad_Id=1 sin importar
    que evento o fecha se compro.
    """
    evento_nombre = (evento_nombre or "Evento").strip()
    fecha_evento  = (fecha_evento  or "").strip()
    lugar         = (lugar or "").strip()

    funcion_id = _generar_funcion_id_estable(evento_nombre, fecha_evento)

    cursor.execute("SELECT Funcion_Id FROM Funcion WHERE Funcion_Id = ?", (funcion_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO Funcion (Funcion_Id, Fecha, Hora, Ciudad) VALUES (?, ?, '', ?)",
            (funcion_id, fecha_evento, lugar)
        )

    cursor.execute("""
        SELECT Funcion_Localidad_Id FROM Funcion_Localidad
        WHERE Funcion_Id = ?
        LIMIT 1
    """, (funcion_id,))
    existente = cursor.fetchone()
    if existente:
        return existente[0]

    # Localidad por defecto para ventas web (general)
    cursor.execute("SELECT Localidad_Id FROM Localidad WHERE LOWER(Nombre) = LOWER('General') LIMIT 1")
    localidad = cursor.fetchone()
    if localidad:
        localidad_id = localidad[0]
    else:
        cursor.execute("INSERT INTO Localidad (Nombre) VALUES ('General')")
        localidad_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO Funcion_Localidad (Funcion_Id, Localidad_Id, Precio, Stock)
        VALUES (?, ?, ?, ?)
    """, (funcion_id, localidad_id, PRECIO_UNITARIO_DEFAULT, 0))

    return cursor.lastrowid


def _asegurar_tabla_ventas_web(cursor):
    """Crea la tabla Ventas_Web si no existe. No toca ninguna tabla existente."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ventas_Web (
            Venta_Id       INTEGER PRIMARY KEY AUTOINCREMENT,
            Usuario_Id     INTEGER,
            Usuario_Correo TEXT,
            Usuario_Nombre TEXT,
            Evento         TEXT,
            Fecha_Evento   TEXT,
            Lugar          TEXT,
            Asientos       TEXT,
            Cantidad       INTEGER,
            Total          REAL,
            Fecha_Compra   TEXT
        )
    """)
    # Agregar Usuario_Id a Ventas_Web si fue creada antes de este cambio
    cols = {f[1] for f in cursor.execute("PRAGMA table_info(Ventas_Web)").fetchall()}
    if "Usuario_Id" not in cols:
        cursor.execute("ALTER TABLE Ventas_Web ADD COLUMN Usuario_Id INTEGER")


def registrar_venta_web(datos):
    """
    Guarda una compra realizada desde el frontend.
    - Resuelve el Usuario_Id real a partir del correo.
    - Inserta en Ventas_Web con Usuario_Id (resumen de la compra).
    - Resuelve/crea la Funcion_Localidad_Id real del evento+fecha comprado
      (en vez del Funcion_Localidad_Id=1 fijo que se usaba antes).
    - Inserta en Boleta una fila POR CADA ASIENTO comprado, guardando
      Boleta_Id (autogenerado), Funcion_Localidad_Id y Usuario_Id.
    """
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        _asegurar_tabla_ventas_web(cursor)
        _asegurar_columnas_boleta(cursor)

        asientos       = datos.get("asientos") or []
        if not isinstance(asientos, list):
            asientos = [asientos] if asientos else []
        asientos_texto = ", ".join(str(a) for a in asientos)

        correo     = datos.get("usuario_correo", "")
        nombre     = datos.get("usuario_nombre", "")
        evento     = datos.get("evento", "")
        fecha_ev   = datos.get("fecha_evento", "")
        lugar      = datos.get("lugar", "")
        cantidad   = datos.get("cantidad", 0) or len(asientos)
        total      = datos.get("total", 0)
        fecha_comp = datos.get("fecha_compra", "")

        # Resolver Usuario_Id real desde la tabla Usuario
        usuario_id = _buscar_usuario_id(cursor, correo)

        # Resolver (o crear) la Funcion_Localidad_Id real del evento+fecha comprado
        funcion_localidad_id = _obtener_o_crear_funcion_localidad(cursor, evento, fecha_ev, lugar)

        # 1. Guardar en Ventas_Web con el ID real del usuario (resumen de la compra)
        cursor.execute("""
            INSERT INTO Ventas_Web
                (Usuario_Id, Usuario_Correo, Usuario_Nombre, Evento, Fecha_Evento,
                 Lugar, Asientos, Cantidad, Total, Fecha_Compra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, correo, nombre, evento, fecha_ev,
              lugar, asientos_texto, cantidad, total, fecha_comp))
        venta_id = cursor.lastrowid

        # 2. Insertar en Boleta una fila por cada asiento: Boleta_Id, Funcion_Localidad_Id, Usuario_Id
        boletas_creadas = []
        asientos_para_boletas = asientos if asientos else [None] * max(cantidad, 1)
        for asiento in asientos_para_boletas:
            cursor.execute("""
                INSERT INTO Boleta (Funcion_Localidad_Id, Usuario_Id, Asiento)
                VALUES (?, ?, ?)
            """, (funcion_localidad_id, usuario_id, str(asiento) if asiento is not None else None))
            boletas_creadas.append(cursor.lastrowid)

        conexion.commit()
        return {
            "id": venta_id,
            "boletas": boletas_creadas,
            "funcion_localidad_id": funcion_localidad_id,
            "usuario_id": usuario_id
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_ventas_usuario(correo):
    """Devuelve todas las compras de un usuario por su correo."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        _asegurar_tabla_ventas_web(cursor)
        cursor.execute("""
            SELECT Evento, Fecha_Evento, Lugar, Asientos, Cantidad, Total, Fecha_Compra
            FROM Ventas_Web
            WHERE Usuario_Correo = ?
            ORDER BY Venta_Id DESC
        """, (correo,))

        filas = cursor.fetchall()
        return [
            {
                "evento":       f[0],
                "fecha_evento": f[1],
                "lugar":        f[2],
                "asientos":     f[3],
                "cantidad":     f[4],
                "total":        f[5],
                "fecha_compra": f[6]
            }
            for f in filas
        ]
    finally:
        conexion.close()