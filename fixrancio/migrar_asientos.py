
"""
Script de migracion (ejecutar UNA SOLA VEZ).
 
Corrige los registros que ya existen en Asiento_Ocupado, los cuales fueron
guardados con Evento_Id=0 y Funcion_Id=0 fijos por el codigo anterior.
Eso hacia que el mismo codigo de asiento (ej. "vip-A1") quedara marcado
como ocupado para TODOS los eventos al mismo tiempo, en vez de solo
para el evento/fecha donde realmente se compro.
 
Como hacerlo:
1. Coloca este archivo en la misma carpeta donde tienes boleteria.db
   (o ajusta RUTA_DB abajo).
2. Reemplaza primero asientos.py por la version corregida.
3. Ejecuta: python migrar_asientos.py
4. Revisa el resumen impreso. Es seguro ejecutarlo mas de una vez.
"""
 
import hashlib
import sqlite3
import os
 
RUTA_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boleteria.db")
 
 
def generar_funcion_id(evento_nombre, fecha_evento):
    clave = f"{evento_nombre.strip().lower()}|{fecha_evento.strip().lower()}"
    digesto = hashlib.sha1(clave.encode("utf-8")).hexdigest()
    return int(digesto[:12], 16)
 
 
def migrar():
    if not os.path.exists(RUTA_DB):
        print(f"No se encontro la base de datos en: {RUTA_DB}")
        print("Edita la variable RUTA_DB en este script con la ruta correcta.")
        return
 
    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()
 
    tablas = {fila[0] for fila in cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
 
    if "Asiento_Ocupado" not in tablas:
        print("La tabla Asiento_Ocupado no existe todavia. No hay nada que migrar.")
        conexion.close()
        return
 
    cursor.execute("""
        SELECT Asiento_Ocupado_Id, Evento_Nombre, Fecha_Evento, Funcion_Id
        FROM Asiento_Ocupado
    """)
    filas = cursor.fetchall()
 
    actualizados = 0
    for fila_id, nombre, fecha, funcion_id_actual in filas:
        nombre = nombre or ""
        fecha = fecha or ""
        if not nombre or not fecha:
            continue
 
        nuevo_funcion_id = generar_funcion_id(nombre, fecha)
        if nuevo_funcion_id != funcion_id_actual:
            cursor.execute(
                "UPDATE Asiento_Ocupado SET Funcion_Id = ? WHERE Asiento_Ocupado_Id = ?",
                (nuevo_funcion_id, fila_id)
            )
            actualizados += 1
 
    conexion.commit()
    conexion.close()
 
    print(f"Migracion completa. Filas revisadas: {len(filas)}. Filas actualizadas: {actualizados}.")
 
 
if __name__ == "__main__":
    migrar()
 