import sys
import os
from tabulate import tabulate

# Configurar rutas
ruta_pruebas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_pruebas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from consultas.proveedores import listar_proveedores, consultar_proveedores_por_evento

print("📦 --- CONSULTANDO MÓDULO DE LOGÍSTICA Y PROVEEDORES --- 🚀\n")

print("📋 --- LISTA GENERAL DE PROVEEDORES ---")
proveedores = listar_proveedores()
if not proveedores:
    print("ℹ️ No hay proveedores registrados individualmente en la tabla Proveedor.")
else:
    print(tabulate(proveedores, headers=["ID", "Nombre Empresa / Proveedor"], tablefmt="grid"))


print("\n🚚 --- ASIGNACIÓN DE LOGÍSTICA POR EVENTO ---")
logistica = consultar_proveedores_por_evento()
if not logistica:
    print("ℹ️ No hay asignaciones registradas en la tabla intermedia Evento_Proveedor.")
else:
    print(tabulate(logistica, headers=["Evento", "Proveedor Asignado"], tablefmt="grid"))