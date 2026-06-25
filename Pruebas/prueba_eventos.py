import sys
import os
from tabulate import tabulate

# Configurar rutas
ruta_pruebas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_pruebas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from consultas.eventos import (
    listar_eventos, 
    buscar_evento, 
    crear_evento, 
    actualizar_evento, 
    eliminar_evento, 
    consultar_aforo
)

print("🚀 --- INICIANDO PRUEBAS DE EVENTOS --- 🚀\n")

# A. Probar Crear Evento
print("1. Creando un evento de prueba temporal (ID: 99)...")
creado = crear_evento(99, 'Concierto de Prueba', '2026-12-31')
if creado: print("✅ Evento creado con éxito.")

# B. Probar Buscar Evento
print("\n2. Buscando el evento creado (ID: 99)...")
evento_buscado = buscar_evento(99)
print(f"🔍 Encontrado: {evento_buscado}")

# C. Probar Actualizar Evento
print("\n3. Actualizando el evento de prueba...")
actualizado = actualizar_evento(99, 'Super Concierto Modificado', '2027-01-01')
if actualizado: print("✅ Evento actualizado con éxito.")

# D. Probar Listar Eventos
print("\n📅 --- LISTA GENERAL DE EVENTOS ---")
eventos = listar_eventos()
print(tabulate(eventos, headers=["ID", "Evento", "Fecha"], tablefmt="grid"))

# E. Probar Consultar Aforo
print("\n🎪 --- REPORTE DE AFORO REAL POR FUNCIÓN ---")
aforos = consultar_aforo()
print(tabulate(aforos, headers=["Evento", "Fecha Función", "Hora", "Boletas Totales"], tablefmt="grid"))

# F. Probar Eliminar Evento (Para limpiar la prueba)
print("\n4. Eliminando el evento de prueba para no ensuciar la BD...")
eliminado = eliminar_evento(99)
if eliminado: print("✅ Evento temporal eliminado correctamente.")