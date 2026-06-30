# -*- coding: utf-8 -*-
"""
limpiar_eventos.py

Borra TODOS los eventos existentes en la base de datos, junto con todo lo
que depende de ellos (proveedores asignados, personal tecnico, riders,
fechas/funciones, boletas y pagos), reutilizando la funcion eliminar_evento()
ya corregida en consultas/eventos.py. No reinventa la logica de borrado: solo
la aplica a todos los Evento_Id que existan hoy.

COMO USARLO
-----------
1. Copia este archivo en la RAIZ de tu proyecto (la misma carpeta donde
   esta app.py, junto a las carpetas 'consultas' y 'utilidades').
2. Cierra Flask antes de correrlo (para evitar que dos procesos escriban
   la base de datos al mismo tiempo).
3. Corre:  python limpiar_eventos.py
4. Revisa el resumen que imprime al final.
5. Vuelve a iniciar Flask normalmente.

Es seguro correrlo mas de una vez: si ya no quedan eventos, simplemente
no hace nada.
"""

import sys
import os

# Asegurar que encuentre las carpetas 'consultas' y 'utilidades' al correr
# este script desde la raiz del proyecto.
RAIZ = os.path.dirname(os.path.abspath(__file__))
if RAIZ not in sys.path:
    sys.path.append(RAIZ)

from utilidades.conexion import conectar
from consultas.eventos import eliminar_evento


def listar_evento_ids():
    """Devuelve la lista de todos los Evento_Id que existen actualmente."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT Evento_Id, Nombre FROM Evento ORDER BY Evento_Id")
        return cursor.fetchall()
    finally:
        conexion.close()


def main():
    eventos = listar_evento_ids()

    if not eventos:
        print("No hay eventos en la base de datos. Nada que limpiar.")
        return

    print(f"Se encontraron {len(eventos)} evento(s) para eliminar:")
    for evento_id, nombre in eventos:
        print(f"  - Evento_Id {evento_id}: {nombre!r}")

    confirmacion = input(
        "\nEsto eliminara TODOS los eventos listados arriba y todo lo "
        "relacionado (proveedores, personal, riders, fechas, boletas y "
        "pagos). Esta accion no se puede deshacer.\n"
        "Escribe 'BORRAR' (en mayusculas) para continuar: "
    )

    if confirmacion.strip() != "BORRAR":
        print("Cancelado. No se borro nada.")
        return

    exitosos = []
    fallidos = []

    for evento_id, nombre in eventos:
        ok = eliminar_evento(evento_id)
        if ok:
            exitosos.append((evento_id, nombre))
            print(f"OK   - Evento_Id {evento_id} ({nombre!r}) eliminado.")
        else:
            fallidos.append((evento_id, nombre))
            print(f"FAIL - Evento_Id {evento_id} ({nombre!r}) NO se pudo eliminar "
                  f"(revisa el mensaje de error impreso arriba por eliminar_evento).")

    print("\n--- Resumen ---")
    print(f"Eliminados correctamente: {len(exitosos)}")
    print(f"Fallidos: {len(fallidos)}")
    if fallidos:
        print("Los siguientes quedaron sin borrar:")
        for evento_id, nombre in fallidos:
            print(f"  - Evento_Id {evento_id}: {nombre!r}")

    restantes = listar_evento_ids()
    print(f"\nEventos que quedan en la base de datos ahora: {len(restantes)}")
    for evento_id, nombre in restantes:
        print(f"  - Evento_Id {evento_id}: {nombre!r}")


if __name__ == "__main__":
    main()