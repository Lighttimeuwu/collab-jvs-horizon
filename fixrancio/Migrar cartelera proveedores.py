"""
migrar_cartelera_proveedores.py
---------------------------------
Migracion para boleteria.db que mueve a SQLite todo lo que el modulo de
Proveedores (JVS FRONTED PROVEEDORES) guardaba unicamente en localStorage
del navegador, causando que los datos no se vieran entre navegadores/sesiones
distintas (ej. un evento publicado por el admin no se veia para el cliente).

Cambios que aplica:

1. Evento.Publicado (columna nueva, INTEGER 0/1, default 0)
   Reemplaza el flag "enCartelera" que vivia en localStorage.cartelera_usuario.
   Un evento con Publicado = 1 es visible para los usuarios finales.

2. Tabla Personal_Tecnico_Evento (nueva)
   Reemplaza el array "personal" que vivia en localStorage.proveedores_data
   por evento. Cada fila es una persona asignada a un evento, con sus
   funciones tecnicas (Audio, Iluminacion, etc.) guardadas como texto
   separado por "|" (formato simple, suficiente para esta lista corta y
   predefinida de funciones; evita una tabla adicional de N-a-N).

3. Proveedor: inserta los 5 proveedores que el frontend de Proveedores ya
   mostraba como opciones hardcodeadas (NovaTech Solutions, Grupo Altiora,
   Impulsa Global, Vertex Consulting, InnovaMax), ADEMAS de los 5 que ya
   existian en la tabla (Audio Pro, Light Show, etc.). No se borra nada
   existente.

La relacion Evento <-> Proveedor ya existia en la tabla Evento_Proveedor
(Evento_Id, Proveedor_Id) y se reutiliza tal cual, sin cambios de esquema.

Es seguro ejecutar este script mas de una vez.

Uso:
    python3 migrar_cartelera_proveedores.py
"""

import os
import sys

ruta_raiz = os.path.dirname(os.path.abspath(__file__))
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from utilidades.conexion import conectar

PROVEEDORES_FRONTEND = [
    ("NovaTech Solutions", "General", "", ""),
    ("Grupo Altiora",      "General", "", ""),
    ("Impulsa Global",     "General", "", ""),
    ("Vertex Consulting",  "General", "", ""),
    ("InnovaMax",          "General", "", ""),
]


def asegurar_columna_publicado(cursor):
    columnas = {fila[1] for fila in cursor.execute("PRAGMA table_info(Evento)").fetchall()}
    if "Publicado" not in columnas:
        cursor.execute("ALTER TABLE Evento ADD COLUMN Publicado INTEGER NOT NULL DEFAULT 0")
        print("✔ Columna Evento.Publicado agregada.")
    else:
        print("✔ Columna Evento.Publicado ya existe.")


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
    print("✔ Tabla Personal_Tecnico_Evento verificada/creada.")


def insertar_proveedores_frontend(cursor):
    cursor.execute("SELECT Nombre FROM Proveedor")
    existentes = {fila[0] for fila in cursor.fetchall()}

    nuevos = [p for p in PROVEEDORES_FRONTEND if p[0] not in existentes]
    if not nuevos:
        print("✔ Los proveedores del frontend ya estaban todos en la tabla Proveedor.")
        return

    cursor.executemany(
        "INSERT INTO Proveedor (Nombre, Servicio, Telefono, Email) VALUES (?, ?, ?, ?)",
        nuevos
    )
    print(f"✔ Proveedores insertados: {[p[0] for p in nuevos]}")


def main():
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        asegurar_columna_publicado(cursor)
        asegurar_tabla_personal_tecnico(cursor)
        insertar_proveedores_frontend(cursor)
        conexion.commit()
        print("\n✅ Migracion completada correctamente.")
    except Exception as error:
        conexion.rollback()
        print(f"\n❌ Error durante la migracion, se revirtio todo: {error}")
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()