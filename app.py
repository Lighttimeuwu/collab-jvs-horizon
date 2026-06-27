import os
import sys

from flask import Flask, jsonify, request, session, redirect, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from consultas.eventos import actualizar_evento_desde_booking, consultar_aforo, listar_eventos, crear_evento_completo
from consultas.usuarios import crear_usuario, validar_login
from consultas.asientos import consultar_asientos_ocupados, registrar_asientos_ocupados
from consultas.ventas import listar_historial_ventas, registrar_venta_web, listar_ventas_usuario
from consultas.proveedores import listar_proveedores, consultar_proveedores_por_evento
from consultas.riders import guardar_rider, obtener_rider, listar_riders, eliminar_rider, guardar_genero_rider


app = Flask(__name__, static_folder=None)

# Cambia esto por algo aleatorio en producción
app.secret_key = os.environ.get("FLASK_SECRET", "jvs-horizon-secret-2025")

ROLES_ADMIN = {1, 2, 3}

# ── Ajusta estas rutas si tus carpetas tienen otro nombre ──────────────────
WEB_DIR     = os.path.join(BASE_DIR, "web")
LOGIN_DIR   = os.path.join(WEB_DIR, "login")
APP_DIR     = os.path.join(WEB_DIR, "app")
ADMIN_DIR   = os.path.join(WEB_DIR, "JVS FRONTED ADMINISTRADOR")
BOOKING_DIR = os.path.join(WEB_DIR, "JVS_FRONTED_BOOKING")
PROVEEDORES_DIR = os.path.join(WEB_DIR, "JVS FRONTED PROVEEDORES")


# ─── Helpers de sesión ───────────────────────────────────────────────────────

def usuario_activo():
    return session.get("usuario")

def es_admin():
    u = usuario_activo()
    return bool(u and u.get("rol_id") in ROLES_ADMIN)


# ─── CORS ─────────────────────────────────────────────────────────────────────

@app.after_request
def permitir_frontend_local(respuesta):
    origen = request.headers.get("Origin", "http://127.0.0.1:5000")
    respuesta.headers["Access-Control-Allow-Origin"]      = origen
    respuesta.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS"
    respuesta.headers["Access-Control-Allow-Headers"]     = "Content-Type"
    respuesta.headers["Access-Control-Allow-Credentials"] = "true"
    return respuesta


# ─── Páginas (protegidas por sesión Flask) ────────────────────────────────────

@app.get("/")
@app.get("/web/login/")
@app.get("/web/login/index.html")
def pagina_login():
    """Si hay sesión activa redirige; si no, muestra el login."""
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


def convertir_evento_a_json(evento):
    """Convierte la tupla de consultas/eventos.py en un objeto JSON claro."""
    evento_id, nombre, fecha, descripcion, hora, lugar, imagen = evento
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
        "funciones": []
    }


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
            session["usuario"] = usuario          # ← abre sesión en el servidor
            return jsonify({"ok": True, "mensaje": "Bienvenido", "usuario": usuario})
        else:
            return jsonify({"ok": False, "error": "Correo o contrasena incorrectos"}), 401

    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/logout")
def cerrar_sesion_api():
    """Destruye la sesión del servidor."""
    session.clear()
    return jsonify({"ok": True})


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


@app.get("/api/proveedores")
def obtener_proveedores_api():
    """Devuelve la lista de proveedores tecnicos registrados."""
    try:
        proveedores = listar_proveedores()
        lista = [{"id": p[0], "nombre": p[1]} for p in proveedores]
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


@app.post("/api/eventos")
def crear_evento_api():
    """Crea un evento nuevo en SQLite desde el formulario Publicar del Rider."""
    try:
        datos = request.get_json(silent=True) or {}
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


@app.get("/api/eventos")
def obtener_eventos():
    """Devuelve eventos reales leidos desde SQLite usando consultas/eventos.py."""
    try:
        eventos = [convertir_evento_a_json(evento) for evento in listar_eventos()]
        eventos_por_nombre = {evento["nombre"]: evento for evento in eventos}

        for nombre, fecha, hora, aforo_total, lugar in consultar_aforo():
            evento = eventos_por_nombre.get(nombre)
            if evento is None:
                continue
            evento["funciones"].append({
                "fecha": fecha,
                "hora": hora,
                "aforo_total": aforo_total,
                "lugar": lugar
            })

        return jsonify({"ok": True, "total": len(eventos), "eventos": eventos})
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


@app.route("/api/asientos-ocupados", methods=["GET", "OPTIONS"])
def obtener_asientos_ocupados_api():
    """Consulta asientos ocupados desde SQLite por evento y fecha (query params)."""
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
    """Devuelve el rider tecnico (incluyendo el archivo) de un artista/evento puntual."""
    try:
        rider = obtener_rider(artista_id)
        if rider is None:
            return jsonify({"ok": False, "error": "No hay rider vinculado para este artista"}), 404
        return jsonify({"ok": True, "rider": rider})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/riders/<artista_id>")
def guardar_rider_api(artista_id):
    """Guarda o reemplaza el rider tecnico vinculado a un artista/evento."""
    try:
        datos = request.get_json(silent=True) or {}
        rider = guardar_rider(
            artista_id,
            datos.get("nombre_archivo"),
            datos.get("tipo_archivo"),
            datos.get("contenido_base64"),
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
    """
    Guarda/actualiza solo el genero musical de un artista/evento,
    sin necesidad de tener ya un archivo de rider subido.
    """
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
        eliminado = eliminar_rider(artista_id)
        if not eliminado:
            return jsonify({"ok": False, "error": "No hay rider vinculado para este artista"}), 404
        return jsonify({"ok": True, "mensaje": "Rider eliminado correctamente"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)