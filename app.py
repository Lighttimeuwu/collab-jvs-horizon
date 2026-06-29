import os
import sys

from flask import Flask, jsonify, request, session, redirect, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

# Cambia esto por algo aleatorio en producción
app.secret_key = os.environ.get("FLASK_SECRET", "jvs-horizon-secret-2025")

ROLES_ADMIN = {1, 2, 3}

# ── Ajusta estas rutas si tus carpetas tienen otro nombre ──────────────────
WEB_DIR         = os.path.join(BASE_DIR, "web")
LOGIN_DIR       = os.path.join(WEB_DIR, "login")
APP_DIR         = os.path.join(WEB_DIR, "app")
ADMIN_DIR       = os.path.join(WEB_DIR, "JVS FRONTED ADMINISTRADOR")
BOOKING_DIR     = os.path.join(WEB_DIR, "JVS_FRONTED_BOOKING")
PROVEEDORES_DIR = os.path.join(WEB_DIR, "JVS FRONTED PROVEEDORES")


# ─── Limpiar eventos vencidos al arrancar ────────────────────────────────────
# Despublica en la DB cualquier evento cuyas fechas ya pasaron,
# antes de atender el primer request.
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


# ─── Sin caché en páginas protegidas por sesión ───────────────────────────────
# Evita que el botón "atrás" del navegador muestre una versión cacheada del
# login/admin/app (bfcache o caché de disco) en vez de volver a pedirle la
# página a Flask. Sin esto, alguien con sesión activa podía "retroceder" y
# ver el formulario de login viejo aunque ya estuviera logueado (o viceversa:
# ver una página protegida tras cerrar sesión).

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
        # El JS guarda esto en catalogoProveedores y lo itera como [[id, nombre], ...]
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
    """
    Devuelve eventos desde SQLite.
    ?publicados=1  → solo los publicados (vista usuario)
    sin parámetro  → todos (panel admin)
    """
    try:
        solo_publicados = request.args.get("publicados") == "1"
        todos = [convertir_evento_a_json(evento) for evento in listar_eventos()]
        if solo_publicados:
            eventos = [e for e in todos if e.get("publicado")]
        else:
            eventos = todos
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


# ─── Publicación a cartelera / proveedores / personal técnico (Proveedores) ──

@app.put("/api/eventos/<int:evento_id>/imagen")
def actualizar_imagen_evento_api(evento_id):
    """
    Recibe una imagen en base64 y la guarda en Evento.Imagen.
    El booking la envía así:
        { "imagen": "data:image/jpeg;base64,/9j/..." }
    """
    try:
        datos  = request.get_json(silent=True) or {}
        imagen = (datos.get("imagen") or "").strip()
        if not imagen:
            return jsonify({"ok": False, "error": "Falta el campo imagen"}), 400
        from consultas.eventos import guardar_imagen_evento
        guardar_imagen_evento(evento_id, imagen)
        return jsonify({"ok": True, "mensaje": "Imagen guardada correctamente", "evento_id": evento_id})
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


# ─── Limpieza automática de eventos vencidos (llamada desde el frontend) ─────

@app.post("/api/eventos/limpiar-vencidos")
def limpiar_eventos_vencidos_api():
    """
    Despublica en la DB todos los eventos cuyas fechas ya pasaron.
    El frontend lo llama silenciosamente al cargar la cartelera,
    para que los eventos vencidos desaparezcan en tiempo real
    sin necesitar reiniciar Flask.
    """
    try:
        vencidos = despublicar_eventos_vencidos()
        return jsonify({"ok": True, "despublicados": vencidos})
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
    """
    Reemplaza los proveedores asignados a un evento. Body esperado:
    { "proveedores": [1, 6] }  ← lista de Proveedor_Id
    """
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
    """
    Agrega una persona de personal tecnico a un evento. Body esperado:
    { "nombre": "Carlos Ramirez", "funciones": ["Audio", "Iluminacion"] }
    """
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


# ─── Gestión de roles (panel administrador) ───────────────────────────────

@app.get("/api/roles")
def obtener_roles_api():
    """Devuelve el catálogo de roles (Administrador, Coordinador, Vendedor, Cliente)."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        roles = listar_roles_catalogo()
        return jsonify({"ok": True, "roles": roles})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.get("/api/usuarios/roles")
def listar_usuarios_roles_api():
    """Devuelve todos los usuarios con su(s) rol(es) actual(es), para el panel de roles."""
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        usuarios = listar_usuarios_con_roles()
        return jsonify({"ok": True, "usuarios": usuarios})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.put("/api/usuarios/<int:usuario_id>/roles")
def asignar_roles_usuario_api(usuario_id):
    """
    Reemplaza el conjunto de roles de un usuario. Body esperado:
    { "roles": [1, 4] }  ← lista de Rol_Id (1=Admin, 2=Coordinador, 3=Vendedor, 4=Cliente)
    Solo accesible para administradores.
    """
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        datos = request.get_json(silent=True) or {}
        roles = datos.get("roles")
        if not isinstance(roles, list):
            return jsonify({"ok": False, "error": "Debe enviar 'roles' como lista de Rol_Id"}), 400

        resultado = asignar_roles_usuario(usuario_id, roles)

        # Si el admin se quita su propio rol de administrador, refrescamos
        # su sesion para que no quede con permisos desincronizados.
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
    """
    Elimina el rider tecnico vinculado a un artista/evento.
    Si el artista_id corresponde a un evento SQLite (formato 'sqlite_X'),
    tambien despublica el evento en la DB para que desaparezca
    inmediatamente de la vista del usuario.
    """
    try:
        # Despublicar el evento en SQLite si el rider pertenece a uno
        if artista_id.startswith("sqlite_"):
            try:
                evento_id = int(artista_id.replace("sqlite_", ""))
                despublicar_evento(evento_id)
            except Exception:
                pass  # Si no existe o ya estaba despublicado, continuar igual

        eliminado = eliminar_rider(artista_id)
        if not eliminado:
            return jsonify({"ok": False, "error": "No hay rider vinculado para este artista"}), 404
        return jsonify({"ok": True, "mensaje": "Rider eliminado correctamente"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.delete("/api/eventos/<int:evento_id>")
def eliminar_evento_api(evento_id):
    """
    Elimina un evento de la DB. Solo admin.
    Despublica primero para que desaparezca de la cartelera del usuario
    antes del borrado fisico.
    """
    if not es_admin():
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        # Despublicar antes de borrar: garantiza que el evento
        # desaparezca de /api/eventos?publicados=1 en ese instante
        try:
            despublicar_evento(evento_id)
        except Exception:
            pass  # Si no existia o ya estaba despublicado, continuar

        eliminado = eliminar_evento(evento_id)
        if not eliminado:
            return jsonify({"ok": False, "error": "El evento no existe"}), 404
        return jsonify({"ok": True, "mensaje": "Evento eliminado"})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)