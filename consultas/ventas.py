import sys
import os

# Asegurar que encuentre la carpeta 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar

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

def _asegurar_tabla_ventas_web(cursor):
    """Crea la tabla Ventas_Web si no existe. No toca ninguna tabla existente."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ventas_Web (
            Venta_Id       INTEGER PRIMARY KEY AUTOINCREMENT,
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


def registrar_venta_web(datos):
    """
    Guarda una compra realizada desde el frontend en la tabla Ventas_Web.
    Recibe un dict con: usuario_correo, usuario_nombre, evento, fecha_evento,
    lugar, asientos (lista), cantidad, total, fecha_compra.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        _asegurar_tabla_ventas_web(cursor)

        asientos = datos.get("asientos") or []
        asientos_texto = ", ".join(asientos) if isinstance(asientos, list) else str(asientos)

        cursor.execute("""
            INSERT INTO Ventas_Web
                (Usuario_Correo, Usuario_Nombre, Evento, Fecha_Evento,
                 Lugar, Asientos, Cantidad, Total, Fecha_Compra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos.get("usuario_correo", ""),
            datos.get("usuario_nombre", ""),
            datos.get("evento", ""),
            datos.get("fecha_evento", ""),
            datos.get("lugar", ""),
            asientos_texto,
            datos.get("cantidad", 0),
            datos.get("total", 0),
            datos.get("fecha_compra", "")
        ))

        conexion.commit()
        return {"id": cursor.lastrowid}
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