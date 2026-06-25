import sys
import os

# Agregamos la carpeta raíz al sistema para que encuentre 'consultas'
ruta_pruebas = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.dirname(ruta_pruebas)
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from consultas.usuarios import listar_usuarios

usuarios = listar_usuarios()

if not usuarios:
    print("📋 La tabla de usuarios está vacía o no tiene registros.")
else:
    print("👥 LISTA DE USUARIOS ENCONTRADOS:")
    for usuario in usuarios:
        print(usuario)