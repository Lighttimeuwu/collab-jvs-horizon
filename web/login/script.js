const API_USUARIOS_URL = "/api/usuarios";

// Esperamos a que el HTML de la página cargue por completo
document.addEventListener("DOMContentLoaded", () => {
  // 1. Leemos los datos del usuario desde la memoria del navegador
  const usuarioString = localStorage.getItem("usuarioLogueado");
  
  if (usuarioString) {
    const usuario = JSON.parse(usuarioString);

    // 2. Si el rol del usuario es 2, ocultamos el contenedor del botón admin
    if (usuario.rol_id === 2) {
      const adminArea = document.getElementById("adminReturnArea");
      if (adminArea) {
        adminArea.style.display = "none"; // Desaparece el botón
      }
    }
  }
});
/* ========================
   GUARDIA: bloquear retroceso si hay sesión activa
   ======================== */
(function bloquearRetrocesoConSesion() {
  const usuario = JSON.parse(localStorage.getItem("usuarioLogueado") || "null");
  if (usuario) {
    history.pushState(null, "", location.href);
    window.addEventListener("popstate", function () {
      history.pushState(null, "", location.href);
    });
  }
})();

/* ========================
   NAVEGACIÓN ENTRE MÓDULOS
   ======================== */

function mostrar(id) {
  document.querySelectorAll(".modulo").forEach(m => m.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

/* ========================
   LOGIN
   ======================== */

const ROLES_ADMIN = [1];

async function login(evento) {
  if (evento) evento.preventDefault();

  const correoInput = document.getElementById("email").value;
  const passInput   = document.getElementById("password").value;
  const error       = document.getElementById("error");

  if (!correoInput || !passInput) {
    error.innerText = "Digita tu correo y contraseña";
    error.style.display = "block";
    return;
  }
  error.style.display = "none";

  const loader = document.getElementById("loader");
  if (loader) loader.style.display = "flex";

  try {
    const respuesta = await fetch("/api/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correo: correoInput, contrasena: passInput })
    });

    const datos = await respuesta.json();
    if (loader) loader.style.display = "none";

    if (datos.ok) {
      localStorage.setItem("usuarioLogueado", JSON.stringify(datos.usuario));

      const rolId = datos.usuario && datos.usuario.rol_id;
      
      // 1. Redirección específica para el Rol 2 (Va directo a Booking)
      if (rolId === 2) {
        window.location.href = "/web/booking/";
        return;
      }

      // 2. Redirección para los Administradores
      if (ROLES_ADMIN.includes(rolId)) {
        localStorage.setItem("admin_sesion_activa", JSON.stringify(datos.usuario));
        window.location.href = "/web/admin/";
        return;
      }
      
      // 3. Redirección por defecto para cualquier otro usuario
      window.location.href = "/web/app/";
      
    } else {
      error.innerText = datos.error || "Correo o contraseña incorrectos";
      error.style.display = "block";
    }
  } catch (err) {
    if (loader) loader.style.display = "none";
    error.innerText = "Error al conectar con el servidor.";
    error.style.display = "block";
  }
}

/* ========================
   REGISTRO
   ======================== */

async function registrarUsuario() {
  const mensaje = document.getElementById("registroMensaje");
  const datos = {
    nombre:     document.getElementById("registroNombre").value.trim(),
    apellido:   document.getElementById("registroApellido").value.trim(),
    correo:     document.getElementById("registroCorreo").value.trim(),
    cedula:     document.getElementById("registroCedula").value.trim(),
    telefono:   document.getElementById("registroTelefono").value.trim(),
    pais:       document.getElementById("pais").value,
    ciudad:     document.getElementById("ciudad").value,
    contrasena: document.getElementById("pass").value.trim()
  };

  if (!datos.nombre || !datos.apellido || !datos.correo || !datos.cedula ||
      !datos.telefono || !datos.pais || !datos.ciudad || !datos.contrasena) {
    mensaje.innerText = "Completa todos los campos para registrarte.";
    mensaje.className = "registro-mensaje error";
    return;
  }

  if (!/^\d{5,15}$/.test(datos.cedula)) {
    mensaje.innerText = "El número de documento debe contener solo dígitos (5 a 15).";
    mensaje.className = "registro-mensaje error";
    return;
  }

  try {
    mensaje.innerText = "Registrando usuario...";
    mensaje.className = "registro-mensaje";

    const respuesta = await fetch(API_USUARIOS_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos)
    });

    const resultado = await respuesta.json();
    if (!respuesta.ok || !resultado.ok) {
      throw new Error(resultado.error || "No se pudo registrar el usuario.");
    }

    mensaje.innerText = "Usuario registrado correctamente.";
    mensaje.className = "registro-mensaje exito";

    document.getElementById("registroNombre").value   = "";
    document.getElementById("registroApellido").value = "";
    document.getElementById("registroCorreo").value   = "";
    document.getElementById("registroCedula").value   = "";
    document.getElementById("registroTelefono").value = "";
    document.getElementById("pass").value             = "";
  } catch (error) {
    mensaje.innerText = error.message || "No se pudo conectar con el servidor.";
    mensaje.className = "registro-mensaje error";
  }
}

/* ========================
   OJO CONTRASEÑA
   ======================== */

function toggleOjo(inputId, btn) {
  const input = document.getElementById(inputId);
  const visible = input.type === "text";
  input.type = visible ? "password" : "text";
  btn.textContent = visible ? "👁️" : "🙈";
}

/* ========================
   CIUDADES POR PAÍS
   ======================== */

function ciudades() {
  const pais = document.getElementById("pais").value;
  const c    = document.getElementById("ciudad");
  c.innerHTML = "";

  const lista = {
    Colombia:  ["Bogotá", "Medellín", "Cali"],
    México:    ["CDMX", "Guadalajara", "Monterrey"],
    España:    ["Madrid", "Barcelona", "Valencia"],
    Argentina: ["Buenos Aires", "Córdoba"],
    Chile:     ["Santiago", "Valparaiso"]
  };

  lista[pais].forEach(ci => {
    const op  = document.createElement("option");
    op.text = ci;
    c.add(op);
  });
}

ciudades();