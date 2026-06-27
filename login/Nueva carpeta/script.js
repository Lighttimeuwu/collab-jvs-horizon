const API_USUARIOS_URL = "http://127.0.0.1:5000/api/usuarios";

/* ========================
   NAVEGACIÓN ENTRE MÓDULOS
   ======================== */

function mostrar(id) {
  document.querySelectorAll(".modulo").forEach(m => m.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function volverAdministrador() {
  localStorage.setItem("admin_entrar_menu", "true");
  window.location.href = "../JVS FRONTED ADMINISTRADOR/index.html";
}

/* ========================
   LOGIN
   ======================== */

// Roles que dan acceso al panel de Administrador (ver tabla Rol):
// 1 = Administrador, 2 = Coordinador de eventos, 3 = Vendedor.
const ROLES_CON_ACCESO_ADMIN = [1, 2, 3];

async function login(evento) {
  if (evento) evento.preventDefault();

  let correoInput = document.getElementById("email").value;
  let passInput   = document.getElementById("password").value;
  let error       = document.getElementById("error");

  if (correoInput === "" || passInput === "") {
    error.innerText = "Digita tu correo y contraseña";
    error.style.display = "block";
    return;
  }
  error.style.display = "none";

  const loader = document.getElementById("loader");
  if (loader) loader.style.display = "flex";

  try {
    const respuesta = await fetch("http://127.0.0.1:5000/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correo: correoInput, contrasena: passInput })
    });

    const datos = await respuesta.json();
    if (loader) loader.style.display = "none";

    if (datos.ok) {
      localStorage.setItem("usuarioLogueado", JSON.stringify(datos.usuario));

      const rolId = datos.usuario && datos.usuario.rol_id;
      if (ROLES_CON_ACCESO_ADMIN.includes(rolId)) {
        // El usuario tiene rol de Administrador/Coordinador/Vendedor:
        // entra directo al panel de Administrador con sesion persistente.
        localStorage.setItem("admin_sesion_activa", JSON.stringify(datos.usuario));
        window.location.href = "../JVS FRONTED ADMINISTRADOR/index.html";
        return;
      }

      // Usuario normal: redirigir al módulo principal
      window.location.href = "../app/index.html";
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
    nombre:    document.getElementById("registroNombre").value.trim(),
    apellido:  document.getElementById("registroApellido").value.trim(),
    correo:    document.getElementById("registroCorreo").value.trim(),
    telefono:  document.getElementById("registroTelefono").value.trim(),
    pais:      document.getElementById("pais").value,
    ciudad:    document.getElementById("ciudad").value,
    contrasena: document.getElementById("pass").value.trim()
  };

  if (!datos.nombre || !datos.apellido || !datos.correo || !datos.telefono || !datos.pais || !datos.ciudad || !datos.contrasena) {
    mensaje.innerText = "Completa todos los campos para registrarte.";
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
    document.getElementById("registroTelefono").value = "";
    document.getElementById("pass").value             = "";
  } catch (error) {
    mensaje.innerText = error.message || "No se pudo conectar con el servidor.";
    mensaje.className = "registro-mensaje error";
  }
}

/* ========================
   CONTRASEÑA
   ======================== */

function togglePass() {
  let p = document.getElementById("pass");
  p.type = p.type === "password" ? "text" : "password";
}

/* ========================
   CIUDADES POR PAÍS
   ======================== */

function ciudades() {
  let pais = document.getElementById("pais").value;
  let c    = document.getElementById("ciudad");
  c.innerHTML = "";

  let lista = {
    Colombia:  ["Bogotá", "Medellín", "Cali"],
    México:    ["CDMX", "Guadalajara", "Monterrey"],
    España:    ["Madrid", "Barcelona", "Valencia"],
    Argentina: ["Buenos Aires", "Córdoba"],
    Chile:     ["Santiago", "Valparaiso"]
  };

  lista[pais].forEach(ci => {
    let op  = document.createElement("option");
    op.text = ci;
    c.add(op);
  });
}

ciudades();
