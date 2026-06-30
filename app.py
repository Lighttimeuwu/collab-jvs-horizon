import os
import sys
import uuid
import base64
import time
import shutil

from flask import Flask, jsonify, request, session, redirect, send_from_directory
from utilidades.conexion import conectar
from utilidades.rutas import ruta_recurso, ruta_persistente

# BASE_DIR: carpeta de RECURSOS DE SOLO LECTURA (web/, plantillas, etc.).
# En modo .exe esto resuelve dentro de sys._MEIPASS (extraccion temporal),
# que es correcto para leer HTML/CSS/JS empaquetados, pero NUNCA debe
# usarse para guardar archivos nuevos (imagenes, riders, base de datos):
# para eso se usa ruta_persistente() mas abajo.
BASE_DIR = ruta_recurso()
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


from consultas.eventos import (
    actualizar_evento_desde_booking, consultar_aforo, listar_eventos,
    crear_evento_completo, publicar_evento, despublicar_evento,
    agregar_personal_tecnico, listar_personal_tecnico, eliminar_personal_tecnico,
    eliminar_evento, despublicar_eventos_vencidos
)
from consultas.usuarios import crear_usuario, validar_login, listar_usuarios_con_roles, listar_roles_catalogo, asignar_roles_usuario
from consultas.asientos import consultar_asientos_ocupados, registrar_asientos_ocupados
from consultas.ventas import listar_historial_ventas, registrar_venta_web, listar_ventas_usuario
from consultas.proveedores import listar_proveedores, consultar_proveedores_por_evento, listar_proveedores_de_evento, asignar_proveedores_evento
from consultas.riders import guardar_rider, obtener_rider, listar_riders, eliminar_rider, guardar_genero_rider


app = Flask(__name__, static_folder=None)

app.secret_key = os.environ.get("FLASK_SECRET", "jvs-horizon-secret-2025")

ROLES_ADMIN = {1, 2, 3}

WEB_DIR         = os.path.join(BASE_DIR, "web")
LOGIN_DIR       = os.path.join(WEB_DIR, "login")
APP_DIR         = os.path.join(WEB_DIR, "app")
ADMIN_DIR       = os.path.join(WEB_DIR, "JVS FRONTED ADMINISTRADOR")
BOOKING_DIR     = os.path.join(WEB_DIR, "JVS_FRONTED_BOOKING")
PROVEEDORES_DIR = os.path.join(WEB_DIR, "JVS FRONTED PROVEEDORES")

# ─── Carpetas físicas para archivos (imágenes de eventos y riders) ──────────
# IMPORTANTE: estas carpetas son donde el usuario SUBE archivos nuevos, así
# que deben vivir junto al .exe real (persistente), no dentro de la carpeta
# temporal de recursos empaquetados, o se perderían al cerrar el programa.
IMAGENES_DIR = ruta_persistente("datos", "imagenes")
os.makedirs(IMAGENES_DIR, exist_ok=True)

RIDERS_DIR = ruta_persistente("datos", "riders")
os.makedirs(RIDERS_DIR, exist_ok=True)


def _migrar_archivos_existentes(carpeta_origen_empaquetada, carpeta_destino_persistente):
    """
    La PRIMERA vez que el .exe corre (carpeta persistente recien creada y
    vacia), copia ahi las imagenes/riders que ya existian en el proyecto
    original y quedaron empaquetadas como recurso de solo lectura dentro
    del .exe. Asi no se "pierden" los archivos que ya tenias subidos antes
    de convertir el proyecto a .exe. En ejecuciones siguientes, como la
    carpeta persistente ya no esta vacia, no vuelve a copiar nada (para
    no pisar archivos nuevos que el usuario haya subido despues).
    """
    if not os.path.isdir(carpeta_origen_empaquetada):
        return
    if os.listdir(carpeta_destino_persistente):
        return  # ya tiene archivos (subidos despues o migrados antes), no tocar

    for nombre in os.listdir(carpeta_origen_empaquetada):
        origen = os.path.join(carpeta_origen_empaquetada, nombre)
        if os.path.isfile(origen):
            shutil.copyfile(origen, os.path.join(carpeta_destino_persistente, nombre))


_migrar_archivos_existentes(ruta_recurso("web", "JVS_FRONTED_BOOKING", "imagenes"), IMAGENES_DIR)
_migrar_archivos_existentes(ruta_recurso("web", "JVS_FRONTED_BOOKING", "riders"), RIDERS_DIR)

EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "webm"}


def guardar_base64_como_archivo(base64_str, carpeta, prefijo):
    """
    Decodifica un string 'data:<mime>;base64,<datos>' y lo guarda como
    archivo físico dentro de 'carpeta'. Solo admite jpg, jpeg, png y webm.
    Devuelve el NOMBRE del archivo guardado (no la ruta completa).
    """
    base64_str = (base64_str or "").strip()
    if not base64_str.startswith("data:"):
        raise ValueError("El contenido debe venir en formato Base64 (data:...)")

    try:
        header, datos_base64 = base64_str.split(",", 1)
        mime = header.split(":")[1].split(";")[0]   # ej: image/png
        extension = mime.split("/")[-1].lower()     # ej: png
    except (ValueError, IndexError):
        raise ValueError("Formato de Base64 inválido")

    if extension == "jpeg":
        extension = "jpg"

    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(
            f"Formato de archivo no permitido: .{extension}. "
            "Solo se aceptan JPG, JPEG, PNG o WEBM."
        )

    nombre_archivo = f"{prefijo}_{uuid.uuid4().hex[:10]}.{extension}"
    ruta_archivo = os.path.join(carpeta, nombre_archivo)

    with open(ruta_archivo, "wb") as f:
        f.write(base64.b64decode(datos_base64))

    return nombre_archivo


# --- Rutas PÚBLICAS para servir archivos (sin restricción de sesión) ---

@app.get("/imagenes/<path:filename>")
def servir_imagenes(filename):
    """Ruta PÚBLICA sin restricción de sesión para que los usuarios puedan ver los flyers."""
    return send_from_directory(IMAGENES_DIR, filename)


@app.get("/riders/<path:filename>")
def servir_riders(filename):
    """Ruta PÚBLICA para que el navegador pueda abrir/mostrar archivos de riders."""
    return send_from_directory(RIDERS_DIR, filename)


# ─── Limpiar eventos vencidos al arrancar ────────────────────────────────────
try:
    despublicar_eventos_vencidos()
except Exception as _e:
    print(f"[inicio] No se pudieron limpiar eventos vencidos: {_e}")


# ─── Helpers de sesión ───────────────────────────────────────────────────────

def usuario_activo():
    return session.get("usuario")

def es_admin():
    u = usuario_activo()
    return bool(u and u.get("rol_id") in ROLES_ADMIN)


# ─── CORS ─────────────────────────────────────────────────────────────────────

@app.after_request
def permitir_frontend_local(respuesta):
    origen = request.headers.get("Origin", f"http://{request.host}")
    respuesta.headers["Access-Control-Allow-Origin"]      = origen
    respuesta.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS"
    respuesta.headers["Access-Control-Allow-Headers"]     = "Content-Type"
    respuesta.headers["Access-Control-Allow-Credentials"] = "true"
    return respuesta


@app.after_request
def evitar_cache_paginas_web(respuesta):
    if request.path.startswith("/web/"):
        respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        respuesta.headers["Pragma"] = "no-cache"
        respuesta.headers["Expires"] = "0"
    return respuesta


# ─── Páginas (protegidas por sesión Flask) ────────────────────────────────────

@app.get("/")
@app.get("/web/login/")
@app.get("/web/login/index.html")
def pagina_login():
    u = usuario_activo()
    if u:
        return redirect("/web/admin/" if u.get("rol_id") in ROLES_ADMIN else "/web/app/")
    return send_from_directory(LOGIN_DIR, "index.html")

@app.get("/web/app/")
@app.get("/web/app/index.html")
def pagina_app():
    if not usuario_activo():
        return redirect("/web/login/")
    return send_from_directory(APP_DIR, "index.html")

@app.get("/web/admin/")
@app.get("/web/admin/index.html")
def pagina_admin():
    if not es_admin():
        return redirect("/web/login/")
    return send_from_directory(ADMIN_DIR, "index.html")

@app.get("/web/booking/")
@app.get("/web/booking/index.html")
def pagina_booking():
    if not es_admin():
        return redirect("/web/login/")
    return send_from_directory(BOOKING_DIR, "index.html")

@app.get("/web/proveedores/")
@app.get("/web/proveedores/index.html")
@app.get("/web/proveedores/proveedores.html")
def pagina_proveedores():
    if not es_admin():
        return redirect("/web/login/")
    return send_from_directory(PROVEEDORES_DIR, "proveedores.html")

@app.get("/web/login/<path:filename>")
def static_login(filename):
    return send_from_directory(LOGIN_DIR, filename)

@app.get("/web/app/<path:filename>")
def static_app(filename):
    if not usuario_activo():
        return redirect("/web/login/")
    return send_from_directory(APP_DIR, filename)

@app.get("/web/admin/<path:filename>")
def static_admin(filename):
    if not es_admin():
        return redirect("/web/login/")
    return send_from_directory(ADMIN_DIR, filename)

@app.get("/web/booking/<path:filename>")
def static_booking(filename):
    if not es_admin():
        return redirect("/web/login/")
    return send_from_directory(BOOKING_DIR, filename)

@app.get("/web/proveedores/<path:filename>")
def static_proveedores(filename):
    if not es_admin():
        return redirect("/web/login/")
    return send_from_directory(PROVEEDORES_DIR, filename)


# ─── Usuarios ─────────────────────────────────────────────────────────────────

@app.route("/api/usuarios", methods=["GET"])
def obtener_correos_usuarios_api():
    """Lista correos de usuarios (utilizado en validaciones de recuperación/registro)."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT Correo FROM Usuario")
        filas = cursor.fetchall()
        correos = [{"correo": fila[0]} for fila in filas]
        return jsonify(correos)
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500
    finally:
        conexion.close()

@app.post("/api/usuarios")
def registrar_usuario():
    """Registra usuarios desde la Vista Usuario y los guarda en SQLite."""
    try:
        datos = request.get_json(silent=True) or {}
        usuario = crear_usuario(datos)
        return jsonify({
            "ok": True,
            "mensaje": "Usuario registrado correctamente",
            "usuario": usuario
        }), 201
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500

@app.put("/api/usuarios/<int:usuario_id>")
def modificar_usuario_api(usuario_id):
    """Modifica la información de un usuario en la DB."""
    datos = request.get_json()
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        from consultas.usuarios import actualizar_usuario
        exito = actualizar_usuario(
            cursor,
            usuario_id,
            datos.get("nombre"),
            datos.get("apellido"),
            datos.get("correo"),
            datos.get("telefono"),
            datos.get("ciudad")
        )
        if not exito:
            return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404
        conexion.commit()
        return jsonify({"ok": True, "mensaje": "Usuario actualizado correctamente"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500
    finally:
        conexion.close()


# ─── Sesión ───────────────────────────────────────────────────────────────────

@app.post("/api/login")
def iniciar_sesion():
    """Valida las credenciales y abre la sesión Flask."""
    try:
        datos = request.get_json(silent=True) or {}
        correo     = datos.get("correo")
        contrasena = datos.get("contrasena")

        if not correo or not contrasena:
            return jsonify({"ok": False, "error": "Faltan credenciales"}), 400

        usuario = validar_login(correo, contrasena)

        if usuario:
            if usuario["estado"] == "Inactivo":
                return jsonify({"ok": False, "error": "Usuario inactivo"}), 403
            session["usuario"] = usuario
            return jsonify({"ok": True, "mensaje": "Bienvenido", "usuario": usuario})
        else:
            return jsonify({"ok": False, "error": "Correo o contrasena incorrectos"}), 401

    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/sesion")
def obtener_sesion():
    """Devuelve los datos del usuario activo para que el frontend los muestre."""
    u = usuario_activo()
    if not u:
        return jsonify({"ok": False, "autenticado": False})
    return jsonify({
        "ok": True,
        "autenticado": True,
        "rol_id": u.get("rol_id"),
        "es_admin": u.get("rol_id") in ROLES_ADMIN,
        "nombre": u.get("nombre"),
        "apellido": u.get("apellido"),
        "cedula": u.get("cedula"),
        "correo": u.get("correo"),
        "telefono": u.get("telefono")
    })

@app.post("/api/logout")
def cerrar_sesion_api():
    """Destruye la sesión del servidor."""
    session.clear()
    return jsonify({"ok": True})


# ─── Eventos ──────────────────────────────────────────────────────────────────

def convertir_evento_a_json(evento):
    """Convierte la tupla de consultas/eventos.py en un objeto JSON claro."""
    evento_id, nombre, fecha, descripcion, hora, lugar, imagen, publicado = evento
    return {
        "id": evento_id,
        "nombre": nombre,
        "fecha": fecha,
        "hora": hora,
        "lugar": lugar,
        "ubicacion": lugar,
        "imagen": imagen,
        "descripcion": descripcion,
        "Descripcion": descripcion,
        "publicado": bool(publicado),
        # ✅ FIX: también exponemos Publicado en mayúsculas para que
        # proveedores.js lo encuentre con cualquiera de las dos grafías.
        "Publicado": 1 if publicado else 0,
        "funciones": []
    }


@app.get("/api/eventos")
def obtener_eventos():
    """
    ✅ FIX: Endpoint único (eliminado el duplicado que pisaba este).
    Devuelve eventos desde SQLite.
      ?publicados=1  → solo los publicados (vista usuario)
      ?ciudad=Bogotá → filtra por ciudad
      sin parámetro  → todos (panel admin / booking / proveedores)
    """
    try:
        solo_publicados = request.args.get("publicados") == "1"
        ciudad_filtrada = request.args.get("ciudad")

        todos = [convertir_evento_a_json(evento) for evento in listar_eventos(ciudad=ciudad_filtrada)]

        if solo_publicados:
            eventos = [e for e in todos if e.get("publicado")]
        else:
            eventos = todos

        eventos_por_id = {evento["id"]: evento for evento in eventos}
        for evento_id, nombre, fecha, hora, aforo_total, lugar in consultar_aforo():
            evento = eventos_por_id.get(evento_id)
            if evento is None:
                continue
            evento["funciones"].append({
                "fecha": fecha, "hora": hora,
                "aforo_total": aforo_total, "lugar": lugar
            })

        return jsonify({"ok": True, "total": len(eventos), "eventos": eventos})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/eventos")
def crear_evento_api():
    """Crea un evento nuevo en SQLite desde el formulario Publicar del Rider."""
    try:
        datos = request.get_json(silent=True) or {}

        # Si la imagen viene en Base64, se clona como archivo físico en /imagenes
        imagen = (datos.get("imagen") or "").strip()
        if imagen.startswith("data:"):
            nombre_archivo = guardar_base64_como_archivo(imagen, IMAGENES_DIR, "evento_nuevo")
            datos["imagen"] = f"/imagenes/{nombre_archivo}"

        evento = crear_evento_completo(datos)
        return jsonify({
            "ok": True,
            "mensaje": "Evento creado correctamente",
            "evento": convertir_evento_a_json(evento)
        }), 201
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/eventos/<int:evento_id>")
def actualizar_evento_api(evento_id):
    """Actualiza un evento real de SQLite desde Booking."""
    try:
        datos = request.get_json(silent=True) or {}
        evento = actualizar_evento_desde_booking(evento_id, datos)
        return jsonify({
            "ok": True,
            "mensaje": "Evento actualizado correctamente",
            "evento": convertir_evento_a_json(evento)
        })
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/eventos/<int:evento_id>/imagen")
def actualizar_imagen_evento_api(evento_id):
    """Recibe una imagen (Base64), la clona como archivo físico y actualiza la BD."""
    try:
        datos  = request.get_json(silent=True) or {}
        imagen = (datos.get("imagen") or "").strip()

        if not imagen:
            return jsonify({"ok": False, "error": "Falta el campo imagen"}), 400

        imagen_final = imagen

        # Si viene en Base64, la convertimos a archivo físico dentro de /imagenes
        if imagen.startswith("data:"):
            nombre_archivo = guardar_base64_como_archivo(imagen, IMAGENES_DIR, f"evento_{evento_id}")
            # Esta es la ruta que se guardará en SQLite (ruta pública)
            imagen_final = f"/imagenes/{nombre_archivo}"

        from consultas.eventos import guardar_imagen_evento
        guardar_imagen_evento(evento_id, imagen_final)

        return jsonify({
            "ok": True,
            "mensaje": "Imagen guardada físicamente",
            "evento_id": evento_id,
            "url_imagen": imagen_final
        })
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500

@app.put("/api/eventos/<int:evento_id>/publicar")
def publicar_evento_api(evento_id):
    """Publica un evento (lo hace visible en la cartelera de usuarios). Solo admin."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        evento = publicar_evento(evento_id)
        return jsonify({"ok": True, "mensaje": "Evento publicado", "evento": convertir_evento_a_json(evento)})
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/eventos/<int:evento_id>/despublicar")
def despublicar_evento_api(evento_id):
    """Retira un evento de la cartelera publica. Solo admin."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        evento = despublicar_evento(evento_id)
        return jsonify({"ok": True, "mensaje": "Evento retirado de cartelera", "evento": convertir_evento_a_json(evento)})
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/eventos/limpiar-vencidos")
def limpiar_eventos_vencidos_api():
    """Despublica en la DB todos los eventos cuyas fechas ya pasaron."""
    try:
        vencidos = despublicar_eventos_vencidos()
        return jsonify({"ok": True, "despublicados": vencidos})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.delete("/api/eventos/<int:evento_id>")
def eliminar_evento_api(evento_id):
    """Elimina un evento de la DB. Solo admin."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        try:
            despublicar_evento(evento_id)
        except Exception:
            pass

        eliminado = eliminar_evento(evento_id)
        if not eliminado:
            return jsonify({"ok": False, "error": "El evento no existe"}), 404
        return jsonify({"ok": True, "mensaje": "Evento eliminado"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


# ─── Proveedores y personal técnico ──────────────────────────────────────────

@app.get("/api/proveedores")
def obtener_proveedores_api():
    """Devuelve la lista de proveedores tecnicos registrados."""
    try:
        proveedores = listar_proveedores()
        lista = [[p[0], p[1]] for p in proveedores]
        return jsonify({"ok": True, "proveedores": lista})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/logistica")
def obtener_logistica_api():
    """Devuelve el cruce de eventos con sus proveedores asignados."""
    try:
        logistica = consultar_proveedores_por_evento()
        lista = [{"evento": l[0], "proveedor": l[1]} for l in logistica]
        return jsonify({"ok": True, "logistica": lista})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/eventos/<int:evento_id>/proveedores")
def obtener_proveedores_evento_api(evento_id):
    """Devuelve los proveedores asignados a un evento puntual."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        proveedores = listar_proveedores_de_evento(evento_id)
        return jsonify({"ok": True, "proveedores": proveedores})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/eventos/<int:evento_id>/proveedores")
def asignar_proveedores_evento_api(evento_id):
    """Reemplaza los proveedores asignados a un evento."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        datos = request.get_json(silent=True) or {}
        proveedores = datos.get("proveedores")
        if not isinstance(proveedores, list):
            return jsonify({"ok": False, "error": "Debe enviar 'proveedores' como lista de Proveedor_Id"}), 400
        resultado = asignar_proveedores_evento(evento_id, proveedores)
        return jsonify({"ok": True, "mensaje": "Proveedores actualizados", **resultado})
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/eventos/<int:evento_id>/personal")
def obtener_personal_tecnico_api(evento_id):
    """Devuelve el personal tecnico asignado a un evento."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        personal = listar_personal_tecnico(evento_id)
        return jsonify({"ok": True, "personal": personal})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/eventos/<int:evento_id>/personal")
def agregar_personal_tecnico_api(evento_id):
    """Agrega una persona de personal tecnico a un evento."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        datos = request.get_json(silent=True) or {}
        resultado = agregar_personal_tecnico(evento_id, datos.get("nombre"), datos.get("funciones"))
        return jsonify({"ok": True, "mensaje": "Personal agregado", "personal": resultado}), 201
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.delete("/api/personal/<int:personal_id>")
def eliminar_personal_tecnico_api(personal_id):
    """Elimina una persona de personal tecnico por su Personal_Id."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        eliminado = eliminar_personal_tecnico(personal_id)
        if not eliminado:
            return jsonify({"ok": False, "error": "No existe esa persona de personal"}), 404
        return jsonify({"ok": True, "mensaje": "Personal eliminado"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


# ─── Asientos ─────────────────────────────────────────────────────────────────

@app.route("/api/asientos-ocupados", methods=["GET", "OPTIONS"])
def obtener_asientos_ocupados_api():
    """Consulta asientos ocupados desde SQLite por evento y fecha."""
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    try:
        datos = {
            "evento":     request.args.get("evento"),
            "fecha":      request.args.get("fecha"),
            "evento_id":  request.args.get("evento_id"),
            "funcion_id": request.args.get("funcion_id")
        }
        resultado = consultar_asientos_ocupados(datos)
        return jsonify({"ok": True, **resultado})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.route("/api/asientos-ocupados", methods=["POST", "OPTIONS"])
def registrar_asientos_ocupados_api():
    """Registra en SQLite los asientos comprados al confirmar una compra."""
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    try:
        datos = request.get_json(silent=True) or {}
        resultado = registrar_asientos_ocupados(datos)
        return jsonify({
            "ok": True,
            "mensaje": "Asientos registrados correctamente",
            **resultado
        }), 201
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


# ─── Ventas ───────────────────────────────────────────────────────────────────

@app.get("/api/ventas")
def obtener_ventas_api():
    """Devuelve el historial de ventas para el panel del Administrador."""
    try:
        ventas = listar_historial_ventas()
        ventas_formateadas = [{"cliente": fila[0], "item": fila[1]} for fila in ventas]
        return jsonify({"ok": True, "ventas": ventas_formateadas})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/ventas/web")
def registrar_venta_web_api():
    """Guarda una compra realizada desde el frontend del usuario."""
    try:
        datos = request.get_json(silent=True) or {}
        resultado = registrar_venta_web(datos)
        return jsonify({"ok": True, **resultado}), 201
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/ventas/usuario/<correo>")
def ventas_usuario_api(correo):
    """Devuelve el historial de compras de un usuario por su correo."""
    try:
        ventas = listar_ventas_usuario(correo)
        return jsonify({"ok": True, "ventas": ventas})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


# ─── Roles ────────────────────────────────────────────────────────────────────

@app.get("/api/roles")
def obtener_roles_api():
    """Devuelve el catálogo de roles."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        roles = listar_roles_catalogo()
        return jsonify({"ok": True, "roles": roles})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/usuarios/roles")
def listar_usuarios_roles_api():
    """Devuelve todos los usuarios con su(s) rol(es) actual(es)."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        usuarios = listar_usuarios_con_roles()
        return jsonify({"ok": True, "usuarios": usuarios})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/usuarios/<int:usuario_id>/roles")
def asignar_roles_usuario_api(usuario_id):
    """Reemplaza el conjunto de roles de un usuario."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        datos = request.get_json(silent=True) or {}
        roles = datos.get("roles")
        if not isinstance(roles, list):
            return jsonify({"ok": False, "error": "Debe enviar 'roles' como lista de Rol_Id"}), 400

        resultado = asignar_roles_usuario(usuario_id, roles)

        u = usuario_activo()
        if u and u.get("id") == usuario_id:
            u["rol_id"] = resultado["rol_id"]
            session["usuario"] = u

        return jsonify({
            "ok": True,
            "mensaje": "Roles actualizados correctamente",
            **resultado
        })
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


# ─── Riders ───────────────────────────────────────────────────────────────────

@app.get("/api/riders")
def listar_riders_api():
    """Devuelve el estado (sin el archivo pesado) de los riders de todos los artistas/eventos."""
    try:
        riders = listar_riders()
        return jsonify({"ok": True, "riders": riders})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/riders/<artista_id>")
def obtener_rider_api(artista_id):
    """Devuelve el rider tecnico (incluyendo la URL del archivo) de un artista/evento puntual."""
    try:
        rider = obtener_rider(artista_id)
        if rider is None:
            return jsonify({"ok": False, "error": "No hay rider vinculado para este artista"}), 404
        return jsonify({"ok": True, "rider": rider})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/riders/<artista_id>")
def guardar_rider_api(artista_id):
    """
    Guarda o reemplaza el rider tecnico vinculado a un artista/evento.
    El archivo llega en Base64, se clona como archivo físico en /web/.../riders
    (solo se admiten jpg, jpeg, png, webm) y en la BD se guarda la ruta pública,
    no el Base64 completo.
    """
    try:
        datos = request.get_json(silent=True) or {}
        contenido_base64 = (datos.get("contenido_base64") or "").strip()
        nombre_original   = datos.get("nombre_archivo")
        tipo_archivo       = datos.get("tipo_archivo")

        ruta_publica = contenido_base64
        if contenido_base64.startswith("data:"):
            nombre_archivo = guardar_base64_como_archivo(contenido_base64, RIDERS_DIR, f"rider_{artista_id}")
            ruta_publica = f"/riders/{nombre_archivo}"

        rider = guardar_rider(
            artista_id,
            nombre_original,
            tipo_archivo,
            ruta_publica,
            datos.get("genero")
        )
        return jsonify({
            "ok": True,
            "mensaje": "Rider guardado correctamente",
            "rider": rider
        }), 201
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/riders/<artista_id>/genero")
def actualizar_genero_rider_api(artista_id):
    """Guarda/actualiza solo el genero musical de un artista/evento."""
    try:
        datos = request.get_json(silent=True) or {}
        resultado = guardar_genero_rider(artista_id, datos.get("genero"))
        return jsonify({
            "ok": True,
            "mensaje": "Genero actualizado correctamente",
            **resultado
        })
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.delete("/api/riders/<artista_id>")
def eliminar_rider_api(artista_id):
    """Elimina el rider tecnico vinculado a un artista/evento."""
    try:
        if artista_id.startswith("sqlite_"):
            try:
                evento_id = int(artista_id.replace("sqlite_", ""))
                despublicar_evento(evento_id)
            except Exception:
                pass

        eliminado = eliminar_rider(artista_id)
        if not eliminado:
            return jsonify({"ok": False, "error": "No hay rider vinculado para este artista"}), 404
        return jsonify({"ok": True, "mensaje": "Rider eliminado correctamente"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


# ─── Recuperación de contraseña ───────────────────────────────────────────────

@app.route("/api/usuarios/contrasena", methods=["PUT"])
def actualizar_pass_recuperacion():
    """Modifica la contraseña del usuario en la base de datos al recuperar contraseña."""
    datos = request.get_json()
    correo = datos.get("correo")
    nueva_pass = datos.get("nueva_contrasena")

    if not correo or not nueva_pass:
        return jsonify({"ok": False, "error": "Faltan datos (correo o contraseña)"}), 400

    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE Usuario
            SET Contrasena = ?
            WHERE Correo = ?
        """, (nueva_pass, correo))

        if cursor.rowcount == 0:
            return jsonify({"ok": False, "error": "Usuario no encontrado con ese correo"}), 404

        conexion.commit()
        return jsonify({"ok": True, "mensaje": "Contraseña actualizada correctamente"})

    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500

    finally:
        conexion.close()


# ─── Herramienta de limpieza de eventos fantasma ─────────────────────────────

@app.route("/api/borrar-fantasma", methods=["GET"])
def borrar_fantasma_manual():
    """Panel rápido para ver y eliminar eventos fantasma de la BD."""
    evento_id = request.args.get("id")
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if evento_id:
            cursor.execute("DELETE FROM Evento WHERE Evento_Id = ?", (evento_id,))
            cursor.execute("DELETE FROM Evento_Artista WHERE Evento_Id = ?", (evento_id,))
            cursor.execute("DELETE FROM Personal_Tecnico_Evento WHERE Evento_Id = ?", (evento_id,))
            conexion.commit()
            return f"""
                <div style="font-family: Arial; padding: 20px;">
                    <h2 style="color: green;">¡Éxito!</h2>
                    <p>El evento con ID <strong>{evento_id}</strong> ha sido eliminado por completo de la base de datos.</p>
                    <a href="/api/borrar-fantasma" style="color: blue; font-weight: bold;">← Volver al listado</a>
                </div>
            """

        cursor.execute("SELECT Evento_Id, Nombre FROM Evento")
        todos_los_eventos = cursor.fetchall()

        html = """
        <div style="font-family: Arial; max-width: 600px; margin: 30px auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px;">
            <h2>Panel de Purga: Eventos en Base de Datos</h2>
            <table border="1" cellpadding="10" style="width: 100%; border-collapse: collapse; text-align: left;">
                <tr style="background-color: #f2f2f2;">
                    <th>ID</th><th>Nombre del Evento</th><th>Acción</th>
                </tr>
        """
        for ev in todos_los_eventos:
            html += f"""
                <tr>
                    <td>{ev[0]}</td>
                    <td><strong>{ev[1]}</strong></td>
                    <td>
                        <a href="/api/borrar-fantasma?id={ev[0]}"
                           style="color: red; font-weight: bold;"
                           onclick="return confirm('¿Eliminar este evento definitivamente?');">
                           ❌ Eliminar
                        </a>
                    </td>
                </tr>
            """
        html += "</table></div>"
        return html

    except Exception as error:
        return f"<h2>Error:</h2><p>{str(error)}</p>"
    finally:
        conexion.close()


@app.after_request
def desactivar_cache_navegador(response):
    """Obliga al navegador a pedir datos nuevos siempre en cada recarga."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    import socket
    import webbrowser
    from threading import Thread
    from utilidades.rutas import _esta_congelado

    URL_INICIO = "http://127.0.0.1:5000/web/login/"

    # El reloader de Flask (activado por debug=True) intenta relanzar el
    # proceso usando sys.executable. En un .exe de PyInstaller eso rompe
    # el programa (se reinicia en bucle o no levanta el servidor) en la
    # PC de destino. Por eso: debug solo en desarrollo, y SIEMPRE con
    # use_reloader=False cuando esta empaquetado como .exe.
    modo_debug = (not _esta_congelado())

    def _esperar_servidor_y_abrir_navegador():
        """
        En vez de abrir el navegador despues de un tiempo fijo (que puede
        ser muy corto la primera vez que el .exe arranca en una PC nueva,
        porque tarda mas en autoextraerse), esperamos activamente a que
        el puerto 5000 realmente este aceptando conexiones, y recien ahi
        abrimos el navegador. Esto evita la pantalla de error del
        navegador por "conexion rechazada" cuando se abre demasiado pronto.
        """
        for _ in range(120):  # hasta ~60 segundos de espera (120 x 0.5s)
            try:
                with socket.create_connection(("127.0.0.1", 5000), timeout=0.5):
                    webbrowser.open(URL_INICIO)
                    return
            except OSError:
                time.sleep(0.5)
        # Si despues de 60s no respondio, igual intentamos abrir por si acaso.
        webbrowser.open(URL_INICIO)

    if _esta_congelado():
        Thread(target=_esperar_servidor_y_abrir_navegador, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=modo_debug, use_reloader=False)