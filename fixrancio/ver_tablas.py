import sqlite3
 
con = sqlite3.connect('boleteria.db')
tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("Tablas encontradas:")
for t in tablas:
    print(" -", t)
con.close()
 