import sqlite3

conexion = sqlite3.connect("boleteria.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# ==========================
# PRODUCTO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Producto (
    Producto_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Producto
VALUES (?,?)
""", [
    (1,'Club Colombia'),
    (2,'Aguila'),
    (3,'Poker'),
    (4,'Antioqueño'),
    (5,'Corona'),
    (6,'Smirnoff'),
    (7,'Costeña'),
    (8,'Nectar'),
    (9,'Whisky'),
    (10,'Amarillo')
])

# ==========================
# INVENTARIO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Inventario (
    Inventario_Id INTEGER PRIMARY KEY,
    Producto_Id INTEGER,
    Stock_Disponible INTEGER,

    FOREIGN KEY (Producto_Id)
    REFERENCES Producto(Producto_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Inventario
VALUES (?,?,?)
""", [
    (1,1,50),
    (2,2,80),
    (3,3,70),
    (4,4,30),
    (5,5,60),
    (6,6,40),
    (7,7,60),
    (8,8,20),
    (9,9,8),
    (10,10,10)
])

# ==========================
# TIPO_MOVIMIENTO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Tipo_Movimiento (
    Tipo_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Tipo_Movimiento
VALUES (?,?)
""", [
    (1,'Ingreso'),
    (2,'Venta')
])

# ==========================
# MOVIMIENTO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Movimiento (
    Movimiento_Id INTEGER PRIMARY KEY,
    Producto_Id INTEGER,
    Tipo_Id INTEGER,
    Cantidad INTEGER,

    FOREIGN KEY (Producto_Id)
    REFERENCES Producto(Producto_Id),

    FOREIGN KEY (Tipo_Id)
    REFERENCES Tipo_Movimiento(Tipo_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Movimiento
VALUES (?,?,?,?)
""", [
    (1,1,2,3),
    (2,2,2,2),
    (3,3,2,5),
    (4,4,2,2),
    (5,5,2,1),
    (6,6,2,3),
    (7,7,2,4),
    (8,8,1,2),
    (9,9,1,5),
    (10,10,2,6)
])

# ==========================
# EVENTO_PRODUCTO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Evento_Producto (
    Evento_Id INTEGER,
    Producto_Id INTEGER,

    PRIMARY KEY (Evento_Id, Producto_Id),

    FOREIGN KEY (Evento_Id)
    REFERENCES Evento(Evento_Id),

    FOREIGN KEY (Producto_Id)
    REFERENCES Producto(Producto_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Evento_Producto
VALUES (?,?)
""", [
    (1,1),
    (2,2),
    (3,3),
    (4,4),
    (5,5),
    (6,6),
    (7,7),
    (8,8),
    (9,9),
    (10,10)
])

conexion.commit()

print("✅ Módulo 3 creado correctamente")
print("✅ Tablas creadas:")
print("   - Producto")
print("   - Inventario")
print("   - Tipo_Movimiento")
print("   - Movimiento")
print("   - Evento_Producto")

conexion.close()