import sqlite3

conexion = sqlite3.connect("boleteria.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# ==========================
# COORDINADOR
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Coordinador (
    Coordinador_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL,
    Apellido TEXT NOT NULL,
    Telefono TEXT,
    Email TEXT
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Coordinador
VALUES (?,?,?,?,?)
""", [
    (1,'Carlos','Gomez','3001111111','carlos@eventos.com'),
    (2,'Laura','Diaz','3002222222','laura@eventos.com'),
    (3,'Juan','Perez','3003333333','juan@eventos.com'),
    (4,'Maria','Lopez','3004444444','maria@eventos.com'),
    (5,'Andres','Torres','3005555555','andres@eventos.com')
])

# ==========================
# PROVEEDOR
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Proveedor (
    Proveedor_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL,
    Servicio TEXT,
    Telefono TEXT,
    Email TEXT
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Proveedor
VALUES (?,?,?,?,?)
""", [
    (1,'Audio Pro','Sonido','3101111111','audio@pro.com'),
    (2,'Light Show','Iluminacion','3102222222','light@show.com'),
    (3,'Security Group','Seguridad','3103333333','security@group.com'),
    (4,'Stage Masters','Tarimas','3104444444','stage@masters.com'),
    (5,'Catering VIP','Alimentos','3105555555','catering@vip.com')
])

# ==========================
# RIDER TECNICO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Rider_Tecnico (
    Rider_Id INTEGER PRIMARY KEY,
    Descripcion TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Rider_Tecnico
VALUES (?,?)
""", [
    (1,'Consola digital y 8 monitores'),
    (2,'Sistema line array completo'),
    (3,'Backline bateria profesional'),
    (4,'Iluminacion inteligente DMX'),
    (5,'Pantallas LED Full HD')
])

# ==========================
# EVENTO_PROVEEDOR
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Evento_Proveedor (
    Evento_Id INTEGER,
    Proveedor_Id INTEGER,

    PRIMARY KEY (Evento_Id, Proveedor_Id),

    FOREIGN KEY (Evento_Id)
    REFERENCES Evento(Evento_Id),

    FOREIGN KEY (Proveedor_Id)
    REFERENCES Proveedor(Proveedor_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Evento_Proveedor
VALUES (?,?)
""", [
    (1,1),
    (1,2),
    (2,3),
    (3,4),
    (4,5),
    (5,1),
    (6,2),
    (7,3),
    (8,4),
    (9,5)
])

# ==========================
# EVENTO_COORDINADOR
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Evento_Coordinador (
    Evento_Id INTEGER,
    Coordinador_Id INTEGER,

    PRIMARY KEY (Evento_Id, Coordinador_Id),

    FOREIGN KEY (Evento_Id)
    REFERENCES Evento(Evento_Id),

    FOREIGN KEY (Coordinador_Id)
    REFERENCES Coordinador(Coordinador_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Evento_Coordinador
VALUES (?,?)
""", [
    (1,1),
    (2,2),
    (3,3),
    (4,4),
    (5,5),
    (6,1),
    (7,2),
    (8,3),
    (9,4),
    (10,5)
])

# ==========================
# ARTISTA_RIDER
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Artista_Rider (
    Artista_Id INTEGER,
    Rider_Id INTEGER,

    PRIMARY KEY (Artista_Id, Rider_Id),

    FOREIGN KEY (Artista_Id)
    REFERENCES Artista(Artista_Id),

    FOREIGN KEY (Rider_Id)
    REFERENCES Rider_Tecnico(Rider_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Artista_Rider
VALUES (?,?)
""", [
    (1,1),
    (2,2),
    (3,3),
    (4,4),
    (5,5),
    (6,1),
    (7,2),
    (8,3),
    (9,4),
    (10,5)
])

conexion.commit()

print("✅ Módulo 5 creado correctamente")
print("✅ Tablas creadas:")
print("   - Coordinador")
print("   - Proveedor")
print("   - Rider_Tecnico")
print("   - Evento_Proveedor")
print("   - Evento_Coordinador")
print("   - Artista_Rider")

conexion.close()