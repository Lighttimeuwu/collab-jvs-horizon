import os
import sys

from flask import Flask, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from consultas.eventos import actualizar_evento_desde_booking, consultar_aforo, listar_eventos, crear_evento_completo
from consultas.usuarios import crear_usuario, validar_login
from consultas.asientos import consultar_asientos_ocupados, registrar_asientos_ocupados
from consultas.ventas import listar_historial_ventas, registrar_venta_web, listar_ventas_usuario
from consultas.proveedores import listar_proveedores, consultar_proveedores_por_evento
from consultas.riders import guardar_rider, obtener_rider, listar_riders, eliminar_rider, guardar_genero_rider


app = Flask(__name__)


@app.after_request
def permitir_frontend_local(respuesta):
    respuesta.headers["Access-Control-Allow-Origin"] = "*"
    respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
    respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return respuesta


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
    """Valida las credenciales enviadas desde el frontend."""
    try:
        datos = request.get_json(silent=True) or {}
        correo = datos.get("correo")
        contrasena = datos.get("contrasena")

        if not correo or not contrasena:
            return jsonify({"ok": False, "error": "Faltan credenciales"}), 400

        usuario = validar_login(correo, contrasena)

        if usuario:
            if usuario["estado"] == "Inactivo":
                return jsonify({"ok": False, "error": "Usuario inactivo"}), 403
            return jsonify({"ok": True, "mensaje": "Bienvenido", "usuario": usuario})
        else:
            return jsonify({"ok": False, "error": "Correo o contrasena incorrectos"}), 401

    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


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


@app.get("/api/asientos-ocupados")
def obtener_asientos_ocupados_api():
    """Consulta asientos ocupados desde SQLite por evento y fecha."""
    try:
        datos = {
            "evento": request.args.get("evento"),
            "fecha":  request.args.get("fecha"),
            "evento_id": request.args.get("evento_id"),
            "funcion_id": request.args.get("funcion_id")
        }
        resultado = consultar_asientos_ocupados(datos)
        return jsonify({"ok": True, **resultado})
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 500


@app.post("/api/asientos-ocupados")
def registrar_asientos_ocupados_api():
    """Registra en SQLite los asientos comprados al confirmar una compra."""
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


@app.get("/")
def inicio():
    return jsonify({
        "ok": True,
        "mensaje": "API de boleteria activa",
        "endpoint_eventos": "/api/eventos"
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)