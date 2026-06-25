import sqlite3

conexion = sqlite3.connect("boleteria.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# ==========================
# GENERO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Genero (
    Genero_Id INTEGER PRIMARY KEY,
    Nombre_Genero TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Genero
VALUES (?,?)
""", [
    (1,'Reggaeton'),
    (2,'Metal'),
    (3,'Bachata'),
    (4,'Techno'),
    (5,'Reggae')
])

# ==========================
# ARTISTA
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Artista (
    Artista_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL,
    Email TEXT,
    Telefono TEXT,
    Genero_Id INTEGER,
    Administrador_Id INTEGER,

    FOREIGN KEY (Genero_Id)
    REFERENCES Genero(Genero_Id),

    FOREIGN KEY (Administrador_Id)
    REFERENCES Administrador(Administrador_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Artista
VALUES (?,?,?,?,?,?)
""", [
    (1,'Mora','mora@gmail.com','3018564428',1,1),
    (2,'Metallica','metallica@gmail.com','3115647755',2,1),
    (3,'Romeo Santos','santos@gmail.com','3128845521',3,1),
    (4,'Bad Bunny','bunny@hotmail.com','3016247898',1,1),
    (5,'Feid','ferxxo@gmail.com','3215468875',1,1),
    (6,'Baswell','baswell@gmail.com','3125786248',4,1),
    (7,'Amelie Lens','amelie@gmail.com','3210545561',4,1),
    (8,'Slipknot','slipknot@gmail.com','3205984259',2,1),
    (9,'Linkin Park','linkin@gmail.com','3054873282',2,1),
    (10,'Zona Ganjah','gajah@gmail.com','3042576264',5,1)
])

# ==========================
# INVITADO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Invitado (
    Invitado_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Invitado
VALUES (?,?)
""", [
    (1,'Ryan Castro'),
    (2,'Pantera'),
    (3,'Prince Royce'),
    (4,'Arcangel'),
    (5,'Karol G'),
    (6,'Cera Khin'),
    (7,'Farrago'),
    (8,'Dragon Force'),
    (9,'Steel Panther'),
    (10,'Morodo')
])

# ==========================
# ARTISTA_INVITADO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Artista_Invitado (
    Artista_Id INTEGER,
    Invitado_Id INTEGER,

    PRIMARY KEY (Artista_Id, Invitado_Id),

    FOREIGN KEY (Artista_Id)
    REFERENCES Artista(Artista_Id),

    FOREIGN KEY (Invitado_Id)
    REFERENCES Invitado(Invitado_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Artista_Invitado
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
# UBICACION
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Ubicacion (
    Ubicacion_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Ubicacion
VALUES (?,?)
""", [
    (1,'Movistar Arena'),
    (2,'Hotel Paradise'),
    (3,'Pradera Box'),
    (4,'Club Campestre'),
    (5,'Trisquel Bar'),
    (6,'Aurora Discoteca'),
    (7,'Plaza Mayor'),
    (8,'Finca Villa Sol'),
    (9,'Parque Simon Bolivar'),
    (10,'Vintage Disco')
])

# ==========================
# EVENTO
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Evento (
    Evento_Id INTEGER PRIMARY KEY,
    Nombre TEXT NOT NULL,
    Fecha TEXT,
    Hora TEXT,
    Stock INTEGER,
    Descripcion TEXT,
    Ubicacion_Id INTEGER,

    FOREIGN KEY (Ubicacion_Id)
    REFERENCES Ubicacion(Ubicacion_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Evento
VALUES (?,?,?,?,?,?,?)
""", [
    (1,'Mora - Estrella Tour 2026','2026-04-15','8:00 PM',5000,'Concierto Estrella Tour',1),
    (2,'Summer Pool Party','2026-05-20','3:00 PM',300,'Fiesta en la piscina DJs invitados',2),
    (3,'Techno Fest V Edicion','2026-06-10','9:00 PM',8000,'Festival de musica techno',3),
    (4,'Show privado empresarial','2026-04-05','7:00 PM',150,'Evento privado para empresa',4),
    (5,'Noche Vallenata VIP','2026-04-18','10:00 PM',400,'Show en vivo de vallenato',5),
    (6,'Reggaeton Party','2026-04-25','11:00 PM',600,'Fiesta temática de reggaeton',6),
    (7,'Festival de Salsa','2026-07-12','6:00 PM',400,'Evento cultural de salsa',7),
    (8,'Pool and Beats','2026-05-30','4:00 PM',340,'Pool party con electrónica',8),
    (9,'Concierto Rock al Parque','2026-06-22','8:30 PM',1200,'Show banda de rock en vivo',9),
    (10,'Fiesta Retro 90s','2026-05-02','9:30 PM',350,'Fiesta temática años 90',10)
])

# ==========================
# EVENTO_ARTISTA
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Evento_Artista (
    Evento_Id INTEGER,
    Artista_Id INTEGER,

    PRIMARY KEY (Evento_Id, Artista_Id),

    FOREIGN KEY (Evento_Id)
    REFERENCES Evento(Evento_Id),

    FOREIGN KEY (Artista_Id)
    REFERENCES Artista(Artista_Id)
)
""")

cursor.executemany("""
INSERT OR IGNORE INTO Evento_Artista
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

print("✅ Módulo 2 creado correctamente")
print("✅ Tablas creadas:")
print("   - Genero")
print("   - Artista")
print("   - Invitado")
print("   - Artista_Invitado")
print("   - Ubicacion")
print("   - Evento")
print("   - Evento_Artista")

conexion.close()