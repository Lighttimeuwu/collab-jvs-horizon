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