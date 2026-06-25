import sys
import os
from tabulate import tabulate

# Configurar rutas
ruta_pruebas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_pruebas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from consultas.ventas import registrar_venta, listar_historial_ventas

print("🛒 --- SIMULANDO PROCESO DE VENTAS (MODO SEGURO) --- 🚀\n")

print("Procesando compra de boleto...")
# Registramos la venta pasando la Boleta 1 y el Usuario 1
venta_exitosa = registrar_venta(boleta_id=1, usuario_id=1)

if venta_exitosa:
    print("✅ ¡Venta registrada exitosamente en tu base de datos!")

print("\n📊 --- REPORTE GENERAL DE TRANSACCIONES ---")
historial = listar_historial_ventas()

if not historial:
    print("ℹ️ No se encontraron registros de ventas en la tabla Detalle_Pago.")
else:
    print(tabulate(historial, headers=["Cliente", "Boleto Adquirido"], tablefmt="grid"))