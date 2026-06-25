import sqlite3

# Crear conexión
conexion = sqlite3.connect("boleteria.db")
cursor = conexion.cursor()

# Activar claves foráneas
cursor.execute("PRAGMA foreign_keys = ON")

# ==========================
# TABLA PAIS
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Pais (
    Pais_Id INTEGER PRIMARY KEY,
    Nombre_Pais TEXT NOT NULL
)
""")

# ==========================
# TABLA USUARIO
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Usuario (
    Usuario_Id INTEGER PRIMARY KEY,
    Cedula INTEGER NOT NULL,
    Nombre TEXT NOT NULL,
    Apellido TEXT NOT NULL,
    Estado TEXT,
    Contrasena TEXT,
    Pais_Id INTEGER,
    FOREIGN KEY (Pais_Id) REFERENCES Pais(Pais_Id)
)
""")

# ==========================
# TABLA TELEFONO
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Telefono (
    Telefono_Id INTEGER PRIMARY KEY,
    Usuario_Id INTEGER,
    Telefono TEXT,
    FOREIGN KEY (Usuario_Id) REFERENCES Usuario(Usuario_Id)
)
""")

# ==========================
# TABLA EMAIL
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Email (
    Email_Id INTEGER PRIMARY KEY,
    Usuario_Id INTEGER,
    Email TEXT,
    FOREIGN KEY (Usuario_Id) REFERENCES Usuario(Usuario_Id)
)
""")

# ==========================
# TABLA ROL
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Rol (
    Rol_Id INTEGER PRIMARY KEY,
    Nombre_Rol TEXT NOT NULL
)
""")

# ==========================
# TABLA ADMINISTRADOR
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Administrador (
    Administrador_Id INTEGER PRIMARY KEY,
    Nombres TEXT,
    Apellidos TEXT
)
""")

# ==========================
# TABLA ADMINISTRADOR_ROL
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS Administrador_Rol (
    Administrador_Id INTEGER,
    Rol_Id INTEGER,
    PRIMARY KEY (Administrador_Id, Rol_Id),
    FOREIGN KEY (Administrador_Id) REFERENCES Administrador(Administrador_Id),
    FOREIGN KEY (Rol_Id) REFERENCES Rol(Rol_Id)
)
""")

# ==========================
# INSERTAR DATOS
# ==========================

cursor.executemany("""
INSERT OR IGNORE INTO Pais
VALUES (?,?)
""", [
    (1,'Japon'),
    (2,'Puerto Rico'),
    (3,'Colombia'),
    (4,'Gran Bretaña'),
    (5,'Inglaterra'),
    (6,'Estados Unidos')
])

cursor.executemany("""
INSERT OR IGNORE INTO Usuario
VALUES (?,?,?,?,?,?,?)
""", [
    (1,111548935,'Itachi','Uchiha','Activo','Itachi2025',1),
    (2,111548936,'Sasuke','Uchiha','Inactivo','Sasuki123',1),
    (3,111548937,'Naruto','Uzumaki','Activo','Boruto1998',3),
    (4,111548938,'Benito','Martinez','Inactivo','Badbo254',2),
    (5,111548956,'Vanesa','Cortes','Inactivo','Millos2045',3),
    (6,111548982,'Juan','Sanabria','Activo','Alimana752',3),
    (7,111548998,'Jhon','Adler','Inactivo','Blackops7752',4),
    (8,111548965,'Steven','Price','Inactivo','Taskforce556',5),
    (9,111548999,'Bruce','Wayne','Activo','Batman2999',6),
    (10,111548952,'Clark','Kent','Activo','Superman2655',6)
])

cursor.executemany("""
INSERT OR IGNORE INTO Telefono
VALUES (?,?,?)
""", [
    (1,1,'3018564429'),
    (2,2,'3115647754'),
    (3,3,'3128845529'),
    (4,4,'3016247890'),
    (5,5,'3215468877'),
    (6,6,'3125786245'),
    (7,7,'3210545566'),
    (8,8,'3205984252'),
    (9,9,'3054873287'),
    (10,10,'3042576264')
])

cursor.executemany("""
INSERT OR IGNORE INTO Email
VALUES (?,?,?)
""", [
    (1,1,'uchiha@gmail.com'),
    (2,2,'uchihas@gmail.com'),
    (3,3,'narutobi@hotmail.com'),
    (4,4,'benito@gmail.com'),
    (5,5,'cortes@hotmail.com'),
    (6,6,'juan@gmail.com'),
    (7,7,'adler@hotmail.com'),
    (8,8,'price@gmail.com'),
    (9,9,'batman@gmail.com'),
    (10,10,'superman@hotmail.com')
])

cursor.executemany("""
INSERT OR IGNORE INTO Rol
VALUES (?,?)
""", [
    (1,'Administrador'),
    (2,'Coordinador de eventos'),
    (3,'Vendedor')
])

cursor.executemany("""
INSERT OR IGNORE INTO Administrador
VALUES (?,?,?)
""", [
    (1,'Julian','Garzon')
])

cursor.executemany("""
INSERT OR IGNORE INTO Administrador_Rol
VALUES (?,?)
""", [
    (1,1),
    (1,2),
    (1,3)
])

conexion.commit()

print("✅ Módulo 1 creado correctamente")
print("✅ Base de datos: boleteria.db")
print("✅ Tablas creadas:")
print("   - Pais")
print("   - Usuario")
print("   - Telefono")
print("   - Email")
print("   - Rol")
print("   - Administrador")
print("   - Administrador_Rol")

conexion.close()