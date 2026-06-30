import sqlite3
import os

# Ajusta esta ruta a donde tengas tu boleteria.db
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boleteria.db")

def publicar_eventos(ids: list[int]):
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró la base de datos en: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(ids))
    cursor.execute(
        f"UPDATE Evento SET Publicado = 1 WHERE Evento_Id IN ({placeholders})",
        ids
    )
    conn.commit()
    afectados = cursor.rowcount

    # Verificar resultado
    cursor.execute(
        f"SELECT Evento_Id, Nombre, Publicado FROM Evento WHERE Evento_Id IN ({placeholders})",
        ids
    )
    rows = cursor.fetchall()
    conn.close()

    print(f"✅ Filas actualizadas: {afectados}")
    print()
    print(f"{'ID':<6} {'Nombre':<30} {'Publicado'}")
    print("-" * 45)
    for evento_id, nombre, publicado in rows:
        estado = "✅ Publicado" if publicado else "❌ No publicado"
        print(f"{evento_id:<6} {nombre:<30} {estado}")

if __name__ == "__main__":
    publicar_eventos([1, 2])