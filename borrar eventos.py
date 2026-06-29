import sqlite3

# Ruta a la base de datos
DB_PATH = "boleteria.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ver cuántos eventos hay antes de borrar
cursor.execute("SELECT Evento_Id, Nombre, Fecha FROM Evento")
eventos = cursor.fetchall()
print(f"Eventos encontrados antes de borrar: {len(eventos)}")
for e in eventos:
    print(f"  ID: {e[0]} | Nombre: {e[1]} | Fecha: {e[2]}")

# Borrar todos los eventos
cursor.execute("DELETE FROM Evento")
conn.commit()

print(f"\n{cursor.rowcount} evento(s) eliminado(s) de la tabla Evento.")

# Verificar que quedó vacía
cursor.execute("SELECT COUNT(*) FROM Evento")
restantes = cursor.fetchone()[0]
print(f"Registros restantes en Evento: {restantes}")

conn.close()