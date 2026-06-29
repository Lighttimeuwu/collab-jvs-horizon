import sys
import os

# Asegurar que encuentre la carpeta 'utilidades'
ruta_consultas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_consultas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar

def listar_proveedores():
    """Trae la lista básica de todos los proveedores registrados en el sistema"""
    conexion = conectar()
    cursor = conexion.cursor()
    
    try:
        # Seleccionamos las columnas estándar que suelen tener (ID y Nombre)
        cursor.execute("""
            SELECT Proveedor_Id, Nombre 
            FROM Proveedor
        """)
        datos = cursor.fetchall()
        return datos
    except Exception as e:
        print(f"❌ Error al listar proveedores: {e}")
        return []
    finally:
        conexion.close()

def consultar_proveedores_por_evento():
    """
    Consulta avanzada: Cruza los eventos con sus proveedores asignados
    para saber quién se encarga de la logística de cada show.
    """
    conexion = conectar()
    cursor = conexion.cursor()
    
    try:
        cursor.execute("""
            SELECT E.Nombre as Evento, P.Nombre as Proveedor
            FROM Evento E
            JOIN Evento_Proveedor EP ON E.Evento_Id = EP.Evento_Id
            JOIN Proveedor P ON EP.Proveedor_Id = P.Proveedor_Id
        """)
        datos = cursor.fetchall()
        return datos
    except Exception as e:
        # Si tu tabla intermedia se llama distinto o está vacía, devuelve una lista segura
        print(f"ℹ️ Nota sobre logística: {e}")
        return []
    finally:
        conexion.close()


def listar_proveedores_de_evento(evento_id):
    """Devuelve los proveedores (id + nombre) asignados a un evento puntual."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            SELECT P.Proveedor_Id, P.Nombre
            FROM Evento_Proveedor EP
            JOIN Proveedor P ON EP.Proveedor_Id = P.Proveedor_Id
            WHERE EP.Evento_Id = ?
            ORDER BY P.Nombre
        """, (evento_id,))
        return [{"proveedor_id": fila[0], "nombre": fila[1]} for fila in cursor.fetchall()]
    finally:
        conexion.close()


def asignar_proveedores_evento(evento_id, proveedor_ids):
    """
    Reemplaza por completo el conjunto de proveedores asignados a un evento
    con la lista de Proveedor_Id dada.
    """
    proveedor_ids = sorted({int(p) for p in (proveedor_ids or [])})

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT Evento_Id FROM Evento WHERE Evento_Id = ?", (evento_id,))
        if not cursor.fetchone():
            raise ValueError("El evento no existe")

        cursor.execute("DELETE FROM Evento_Proveedor WHERE Evento_Id = ?", (evento_id,))
        cursor.executemany(
            "INSERT OR IGNORE INTO Evento_Proveedor (Evento_Id, Proveedor_Id) VALUES (?, ?)",
            [(evento_id, proveedor_id) for proveedor_id in proveedor_ids]
        )
        conexion.commit()
        return {"evento_id": evento_id, "proveedores": proveedor_ids}
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()