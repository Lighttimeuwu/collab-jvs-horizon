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

    // Indicamos éxito de creación en el mensajito
    mensaje.innerText = "¡Usuario creado satisfactoriamente!";
    mensaje.className = "registro-mensaje exito";

    // Limpiamos los campos
    document.getElementById("registroNombre").value   = "";
    document.getElementById("registroApellido").value = "";
    document.getElementById("registroCorreo").value   = "";
    document.getElementById("registroCedula").value   = "";
    document.getElementById("registroTelefono").value = "";
    document.getElementById("pass").value             = "";
    
    // Esperamos 2 segundos para que el usuario visualice el mensaje y luego redirigimos al login
    setTimeout(() => {
      mostrar('login');
      mensaje.innerText = ""; // Limpiamos el mensaje para cuando vuelvan a abrir el formulario
    }, 2000);

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


/* ==================================================
   LÓGICA DE RECUPERACIÓN DE CONTRASEÑA (PROTOTIPO)
   ================================================== */

let correoEnRecuperacion = "";

async function enviarCodigoRecuperacion() {
  const correo = document.getElementById("recuperarCorreo").value.trim();
  const mensaje = document.getElementById("recuperarMensaje");

  if (!correo) {
    mensaje.innerText = "Por favor ingresa un correo electrónico.";
    mensaje.className = "registro-mensaje error";
    return;
  }

  try {
    mensaje.innerText = "Verificando correo...";
    mensaje.className = "registro-mensaje";

    // 1. Consultamos la lista de usuarios para verificar si existe en BD
    const respuesta = await fetch(API_USUARIOS_URL);
    const usuarios = await respuesta.json();
    
    // Asumimos que la API devuelve un array o un objeto con usuarios
    const listaUsuarios = Array.isArray(usuarios) ? usuarios : (usuarios.usuarios || []);
    const usuarioEncontrado = listaUsuarios.find(u => u.correo === correo || u.Correo === correo);

    if (!usuarioEncontrado) {
      throw new Error("El correo ingresado no se encuentra registrado.");
    }

    // 2. Guardamos el correo y pasamos a la pantalla de validación de código
    correoEnRecuperacion = correo;
    alert("Código simulado generado para pruebas: 123456");
    
    document.getElementById("recuperarCorreo").value = "";
    mensaje.innerText = "";
    mostrar('validarCodigo');

  } catch (error) {
    mensaje.innerText = error.message;
    mensaje.className = "registro-mensaje error";
  }
}

function verificarCodigo() {
  const codigo = document.getElementById("codigoIngresado").value.trim();
  const mensaje = document.getElementById("codigoMensaje");

  // Usamos "123456" simulando la clave de recuperación del correo
  if (codigo === "123456") {
    document.getElementById("codigoIngresado").value = "";
    mensaje.innerText = "";
    mostrar('nuevaPass');
  } else {
    mensaje.innerText = "Código incorrecto. En un entorno real, verifica tu bandeja.";
    mensaje.className = "registro-mensaje error";
  }
}

async function actualizarContrasena() {
  const nuevaPass = document.getElementById("nuevaContrasena").value.trim();
  const confirmaPass = document.getElementById("confirmaContrasena").value.trim();
  const mensaje = document.getElementById("nuevaPassMensaje");

  if (!nuevaPass || !confirmaPass) {
    mensaje.innerText = "Por favor, llena ambos campos.";
    mensaje.className = "registro-mensaje error";
    return;
  }

  if (nuevaPass !== confirmaPass) {
    mensaje.innerText = "Las contraseñas no coinciden.";
    mensaje.className = "registro-mensaje error";
    return;
  }

  try {
    mensaje.innerText = "Actualizando contraseña en base de datos...";
    mensaje.className = "registro-mensaje";

    // Realizamos la petición PUT a la API
    const respuesta = await fetch("/api/usuarios/contrasena", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        correo: correoEnRecuperacion, 
        nueva_contrasena: nuevaPass 
      })
    });

    const resultado = await respuesta.json();
    if (!resultado.ok) {
      throw new Error(resultado.error || "No se pudo actualizar la contraseña.");
    }
    
    alert("¡Contraseña actualizada correctamente en la base de datos!");
    
    document.getElementById("nuevaContrasena").value = "";
    document.getElementById("confirmaContrasena").value = "";
    mensaje.innerText = "";
    correoEnRecuperacion = "";
    
    mostrar('login');

  } catch (error) {
    mensaje.innerText = error.message || "No se pudo actualizar la contraseña.";
    mensaje.className = "registro-mensaje error";
  }
}

async function enviarActualizacionUsuario(usuarioId, datosNuevos) {
  try {
    const respuesta = await fetch(`/api/usuarios/${usuarioId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosNuevos)
    });
    
    const resultado = await respuesta.json();
    if (resultado.ok) {
      alert("¡Datos actualizados con éxito!");
    } else {
      alert("Error: " + resultado.error);
    }
  } catch (error) {
    console.error("Error de conexión:", error);
  }
}