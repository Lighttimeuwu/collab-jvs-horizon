import sqlite3

conexion = sqlite3.connect("boleteria.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# ==========================
# FUNCION
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Funcion (
    Funcion_Id INTEGER PRIMARY KEY,
    Fecha TEXT,
    Hora TEXT
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Funcion
VALUES (?,?,?)
""", [
    (1,'2026-04-15','8:00 PM'),
    (2,'2026-05-20','3:00 PM'),
    (3,'2026-06-10','9:00 PM'),
    (4,'2026-04-05','7:00 PM'),
    (5,'2026-04-18','10:00 PM'),
    (6,'2026-04-25','11:00 PM'),
    (7,'2026-07-12','6:00 PM'),
    (8,'2026-05-30','4:00 PM'),
    (9,'2026-06-22','8:30 PM'),
    (10,'2026-05-02','9:30 PM')
])

# ==========================
# LOCALIDAD
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Localidad (
    Localidad_Id INTEGER PRIMARY KEY,
    Nombre TEXT
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Localidad
VALUES (?,?)
""", [
    (1,'Platea'),
    (2,'Habitacion 301'),
    (3,'Backstage'),
    (4,'Mesa 4'),
    (5,'Mesa 10'),
    (6,'Mesa 22'),
    (7,'General'),
    (8,'Cabaña 3'),
    (9,'VIP'),
    (10,'Mesa 8')
])

# ==========================
# FUNCION_LOCALIDAD
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Funcion_Localidad (
    Funcion_Localidad_Id INTEGER PRIMARY KEY,
    Funcion_Id INTEGER,
    Localidad_Id INTEGER,
    Precio REAL,
    Stock INTEGER,

    FOREIGN KEY (Funcion_Id)
    REFERENCES Funcion(Funcion_Id),

    FOREIGN KEY (Localidad_Id)
    REFERENCES Localidad(Localidad_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Funcion_Localidad
VALUES (?,?,?,?,?)
""", [
    (1,1,1,450000,14000),
    (2,2,2,500000,10000),
    (3,3,3,600000,14000),
    (4,4,4,350000,5000),
    (5,5,5,520000,14000),
    (6,6,6,360000,14000),
    (7,7,7,540000,14000),
    (8,8,8,600000,14000),
    (9,9,9,450000,14000),
    (10,10,10,320000,14000)
])

# ==========================
# BOLETA
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Boleta (
    Boleta_Id INTEGER PRIMARY KEY,
    Funcion_Localidad_Id INTEGER,

    FOREIGN KEY (Funcion_Localidad_Id)
    REFERENCES Funcion_Localidad(Funcion_Localidad_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Boleta
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

# ==========================
# PASARELA_PAGO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Pasarela_Pago (
    Pasarela_Id INTEGER PRIMARY KEY,
    Metodo_Pago TEXT,
    Fecha TEXT
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Pasarela_Pago
VALUES (?,?,?)
""", [
    (1,'PSE','2026-04-15')
])

# ==========================
# DETALLE_PAGO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Detalle_Pago (
    Detalle_Id INTEGER PRIMARY KEY,
    Pasarela_Id INTEGER,
    Funcion_Localidad_Id INTEGER,
    Cantidad INTEGER,
    Usuario_Id INTEGER,

    FOREIGN KEY (Pasarela_Id)
    REFERENCES Pasarela_Pago(Pasarela_Id),

    FOREIGN KEY (Funcion_Localidad_Id)
    REFERENCES Funcion_Localidad(Funcion_Localidad_Id),

    FOREIGN KEY (Usuario_Id)
    REFERENCES Usuario(Usuario_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Detalle_Pago
VALUES (?,?,?,?,?)
""", [
    (1,1,1,1,1),
    (2,1,2,4,2),
    (3,1,3,3,3),
    (4,1,4,1,4),
    (5,1,5,5,5),
    (6,1,6,2,6),
    (7,1,7,1,7),
    (8,1,8,1,8),
    (9,1,9,3,9),
    (10,1,10,1,10)
])

# ==========================
# EVENTO_BOLETA
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Evento_Boleta (
    Evento_Id INTEGER,
    Boleta_Id INTEGER,

    PRIMARY KEY (Evento_Id, Boleta_Id),

    FOREIGN KEY (Evento_Id)
    REFERENCES Evento(Evento_Id),

    FOREIGN KEY (Boleta_Id)
    REFERENCES Boleta(Boleta_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Evento_Boleta
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

print("✅ Módulo 4 creado correctamente")
print("✅ Tablas creadas:")
print("   - Funcion")
print("   - Localidad")
print("   - Funcion_Localidad")
print("   - Boleta")
print("   - Pasarela_Pago")
print("   - Detalle_Pago")
print("   - Evento_Boleta")

conexion.close()