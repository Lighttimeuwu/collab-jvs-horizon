/* ========================
   ESTADO
   ======================== */

let eventos = [];                  // cache de GET /api/eventos
let catalogoProveedores = [];       // cache de GET /api/proveedores
let currentEvent = null;            // Evento_Id (numero) del modulo de personal abierto
let currentEventName = "";
let currentProviderEvent = null;    // Evento_Id (numero) del editor de proveedores abierto

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

const FUNCIONES_TECNICAS = [
  "Bocinas y Subwoofers",
  "Consola de mezcla",
  "Microfonos",
  "Luces LED y Wash",
  "Cabezas moviles/Roboticas",
  "Consola DMX",
  "Maquina de humo",
  "Pantallas LED",
  "Escenario (Tarimas)",
  "Tripodes y Stands",
  "Cableado y conectividad"
];

/* ========================
   HELPERS
   ======================== */

function escaparHTML(valor = "") {
  return String(valor)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function buscarEvento(eventoId) {
  return eventos.find(evento => evento.id === eventoId);
}

async function peticionJSON(url, opciones = {}) {
  const respuesta = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...opciones
  });
  const datos = await respuesta.json();
  if (!respuesta.ok || !datos.ok) {
    throw new Error(datos.error || `Error en ${url}`);
  }
  return datos;
}

/* ========================
   CARGA INICIAL
   ======================== */

async function cargarDatosIniciales() {
  try {
    // Traemos los datos frescos rompiendo la caché
    const [datosEventos, datosProveedores] = await Promise.all([
      peticionJSON("/api/eventos?t=" + Date.now()),
      peticionJSON("/api/proveedores?t=" + Date.now())
    ]);
    
    // Proveedores es una vista de administración: mostramos TODOS los eventos
    // (publicados o no) para que el admin pueda asignar proveedores, personal y riders
    // antes de publicarlos en cartelera.
    eventos = datosEventos.eventos || [];
    
    catalogoProveedores = datosProveedores.proveedores || [];
    renderEventList();
  } catch (error) {
    const contenedor = document.getElementById("eventList");
    if (contenedor) {
      contenedor.innerHTML = `<p class="provider-empty">No se pudieron cargar los eventos: ${error.message}</p>`;
    }
  }
}

/* ========================
   LISTA DE EVENTOS
   ======================== */

function renderEventList() {
  const contenedor = document.getElementById("eventList");

  if (!eventos.length) {
    contenedor.innerHTML = `<p class="provider-empty">Todavia no hay eventos creados desde Booking.</p>`;
    return;
  }

  contenedor.innerHTML = eventos.map(evento => {
    const estaPublicado = evento.publicado || evento.Publicado === 1;
    return `
    <div class="event" onclick="openModule(${evento.id}, '${escaparJS(evento.nombre)}')">
      <img src="${escaparHTML(evento.imagen || '')}" alt="${escaparHTML(evento.nombre)}">
      <h3>${escaparHTML(evento.nombre)}</h3>
      ${evento.lugar ? `<p class="event-place">${escaparHTML(evento.lugar)}</p>` : ""}
      <div id="empresas-evento-${evento.id}" class="provider-tags-wrapper">Cargando proveedores...</div>
      ${estaPublicado
        ? `<p class="sent-board-status">✅ Publicado en cartelera</p>`
        : `<p class="sent-board-status" style="background:rgba(150,80,0,0.85);">⏳ Borrador</p>`}
      <div class="event-actions">
        <button class="provider-card-btn" onclick="abrirEditorProveedores(event, ${evento.id}, '${escaparJS(evento.nombre)}')">Asignar proveedores</button>
      </div>
    </div>
  `}).join("");

  eventos.forEach(evento => cargarYRenderEmpresasEvento(evento.id));
}

async function cargarYRenderEmpresasEvento(eventoId) {
  const contenedor = document.getElementById(`empresas-evento-${eventoId}`);
  if (!contenedor) return;
  try {
    const datos = await peticionJSON(`/api/eventos/${eventoId}/proveedores`);
    const proveedores = datos.proveedores || [];
    contenedor.innerHTML = proveedores.length
      ? `<div class="provider-tags">${proveedores.map(p => `<span>${escaparHTML(p.nombre)}</span>`).join("")}</div>`
      : `<p class="provider-empty">Sin proveedor asignado</p>`;
  } catch (error) {
    contenedor.innerHTML = `<p class="provider-empty">No se pudo cargar</p>`;
  }
}

/* ========================
   MODULO: PERSONAL TECNICO
   ======================== */

function openModule(eventoId, eventoNombre) {
  currentEvent = eventoId;
  currentEventName = eventoNombre;

  document.getElementById("eventTitle").innerText = "Evento: " + eventoNombre;
  document.getElementById("module").style.display = "block";
  document.getElementById("providerModule").style.display = "none";
  document.getElementById("eventList").style.display = "none";
  document.getElementById("adminReturnArea").style.display = "none";

  render();
}

async function render() {
  const evento = buscarEvento(currentEvent);
  const publicado = evento ? (evento.publicado || evento.Publicado === 1) : false;

  document.getElementById("content").innerHTML = `
    <div class="section">
      <h4>🎵 Rider Técnico del Evento</h4>
      <div id="riderInfo" style="
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,191,0,0.35);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
        min-height: 48px;
      ">Cargando rider...</div>
    </div>

    <div class="section">
      <h4>Personal Tecnico</h4>
      <p class="helper-text">Selecciona las funciones de cada persona y agrega su nombre.</p>
      <div class="roles-checkboxes" id="funcionesCheckboxes">
        ${FUNCIONES_TECNICAS.map(funcion => `
          <label class="rol-checkbox-label">
            <input type="checkbox" value="${escaparHTML(funcion)}">
            ${escaparHTML(funcion)}
          </label>
        `).join("")}
      </div>
      <div id="personalList">Cargando personal...</div>
      <input type="text" id="newPerson" placeholder="Nombre de la persona">
      <button onclick="addPerson()">Agregar</button>
    </div>

    <div class="module-board-actions">
      ${publicado
        ? `<p class="sent-board-status in-module">Publicado en cartelera</p>`
        : `<button class="send-board-btn" id="btnPublicar" onclick="publicarEventoActual()">Publicar en cartelera</button>`}
    </div>
  `;

  await Promise.all([
    cargarYRenderPersonal(),
    cargarYRenderRider()
  ]);
}

/* ========================
   RIDER TÉCNICO (solo lectura en Proveedores)
   ======================== */

async function cargarYRenderRider() {
  const contenedor = document.getElementById("riderInfo");
  if (!contenedor) return;

  // El rider se guarda en Booking con la clave "sqlite_<id>",
  // por eso construimos el artista_id del mismo modo.
  const artistaId = "sqlite_" + currentEvent;

  try {
    const respuesta = await fetch(`/api/riders/${encodeURIComponent(artistaId)}`);
    const datos = await respuesta.json();

    if (!respuesta.ok || !datos.ok || !datos.rider) {
      contenedor.innerHTML = `<em style="color:#bbb;">Sin rider técnico vinculado para este evento.</em>`;
      return;
    }

    const rider = datos.rider;
    // contenido_base64 ahora es la URL pública del archivo físico
    // (ej. /riders/rider_sqlite_7_a1b2c3.png), no un data-URI.
    const urlArchivo = rider.contenido_base64;
    const tieneArchivo = Boolean(rider.nombre_archivo && urlArchivo);
    const genero = rider.genero || "—";

    contenedor.innerHTML = `
      <div style="display:flex; flex-wrap:wrap; gap:18px; align-items:center;">
        <div>
          <span style="color:#ffbf00; font-weight:bold;">Género musical:</span>
          <span style="margin-left:6px;">${escaparHTML(genero)}</span>
        </div>
        <div>
          <span style="color:#ffbf00; font-weight:bold;">Archivo:</span>
          <span style="margin-left:6px; color:${tieneArchivo ? '#4CAF50' : '#e57373'};">
            ${tieneArchivo ? '✅ ' + escaparHTML(rider.nombre_archivo) : '❌ Sin archivo'}
          </span>
        </div>
        ${tieneArchivo ? `
        <button
          onclick="abrirRiderProveedores('${escaparJS(urlArchivo)}')"
          style="background:#2196F3; color:white; border:none; padding:6px 14px; border-radius:6px; cursor:pointer; font-weight:bold;">
          👁️ Abrir rider
        </button>` : ""}
      </div>
    `;
  } catch (error) {
    contenedor.innerHTML = `<em style="color:#bbb;">No se pudo consultar el rider: ${escaparHTML(error.message)}</em>`;
  }
}

function escaparJS(valor = "") {
  return String(valor).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

function abrirRiderProveedores(urlArchivo) {
  if (!urlArchivo) {
    alert("No hay archivo vinculado.");
    return;
  }
  // El archivo ahora es una imagen física servida por el backend
  // (/riders/<archivo>), así que simplemente la abrimos en una pestaña nueva.
  const ventana = window.open(urlArchivo, "_blank");
  if (!ventana) {
    alert("El navegador bloqueó la ventana emergente. Permite ventanas emergentes para este sitio.");
  }
}

async function cargarYRenderPersonal() {
  const contenedor = document.getElementById("personalList");
  if (!contenedor) return;
  try {
    const datos = await peticionJSON(`/api/eventos/${currentEvent}/personal`);
    renderPersonal(datos.personal || []);
  } catch (error) {
    contenedor.innerHTML = `<p class="empty-personal">No se pudo cargar el personal.</p>`;
  }
}

function renderPersonal(personal) {
  const contenedor = document.getElementById("personalList");
  if (!contenedor) return;

  if (!personal.length) {
    contenedor.innerHTML = `<p class="empty-personal">No hay personal asignado.</p>`;
    return;
  }

  contenedor.innerHTML = personal.map(persona => {
    const funciones = persona.funciones && persona.funciones.length
      ? persona.funciones.map(f => `<span>${escaparHTML(f)}</span>`).join("")
      : `<em>Sin funciones seleccionadas</em>`;

    return `
      <div class="personal-item">
        <div>
          <b>${escaparHTML(persona.nombre)}</b>
          <div class="funciones-personal">${funciones}</div>
        </div>
        <button onclick="removePerson(${persona.personal_id})">X</button>
      </div>
    `;
  }).join("");
}

async function addPerson() {
  const input = document.getElementById("newPerson");
  const nombre = input.value.trim();
  if (!nombre) return;

  const funciones = Array.from(document.querySelectorAll("#funcionesCheckboxes input:checked"))
    .map(el => el.value);

  try {
    await peticionJSON(`/api/eventos/${currentEvent}/personal`, {
      method: "POST",
      body: JSON.stringify({ nombre, funciones })
    });
    input.value = "";
    document.querySelectorAll("#funcionesCheckboxes input:checked").forEach(el => { el.checked = false; });
    await cargarYRenderPersonal();
  } catch (error) {
    alert("No se pudo agregar el personal: " + error.message);
  }
}

async function removePerson(personalId) {
  try {
    await peticionJSON(`/api/personal/${personalId}`, { method: "DELETE" });
    await cargarYRenderPersonal();
  } catch (error) {
    alert("No se pudo eliminar: " + error.message);
  }
}

/* ========================
   PUBLICAR A CARTELERA
   ======================== */

async function publicarEventoActual() {
  try {
    const datosProveedores = await peticionJSON(`/api/eventos/${currentEvent}/proveedores`);
    const datosPersonal = await peticionJSON(`/api/eventos/${currentEvent}/personal`);

    if (!(datosProveedores.proveedores || []).length) {
      alert("Primero asigna al menos un proveedor a este evento.");
      return;
    }
    if (!(datosPersonal.personal || []).length) {
      alert("Primero agrega al menos una persona de personal tecnico.");
      return;
    }

    await peticionJSON(`/api/eventos/${currentEvent}/publicar`, { method: "PUT" });
    alert("Evento publicado en la cartelera de usuarios.");

    const evento = buscarEvento(currentEvent);
    if (evento) evento.publicado = true;
    await render();
  } catch (error) {
    alert("No se pudo publicar el evento: " + error.message);
  }
}

/* ========================
   MODULO: PROVEEDORES
   ======================== */

function abrirEditorProveedores(eventoClick, eventoId, eventoNombre) {
  eventoClick.stopPropagation();
  currentProviderEvent = eventoId;

  document.getElementById("providerTitle").innerText = "Proveedores: " + eventoNombre;
  document.getElementById("eventList").style.display = "none";
  document.getElementById("adminReturnArea").style.display = "none";
  document.getElementById("module").style.display = "none";
  document.getElementById("providerModule").style.display = "block";

  renderOpcionesEmpresas();
}

async function renderOpcionesEmpresas() {
  const contenedor = document.getElementById("providerOptions");
  contenedor.innerHTML = "Cargando proveedores...";

  try {
    const datos = await peticionJSON(`/api/eventos/${currentProviderEvent}/proveedores`);
    const seleccionados = new Set((datos.proveedores || []).map(p => p.proveedor_id));

    contenedor.innerHTML = catalogoProveedores.map(([id, nombre]) => {
      const checked = seleccionados.has(id) ? "checked" : "";
      return `
        <label class="provider-option">
          <input type="checkbox" value="${id}" ${checked}>
          <span>${escaparHTML(nombre)}</span>
        </label>
      `;
    }).join("");
  } catch (error) {
    contenedor.innerHTML = `<p class="provider-empty">No se pudo cargar: ${escaparHTML(error.message)}</p>`;
  }
}

async function guardarEmpresasEvento() {
  const proveedorIds = Array.from(document.querySelectorAll("#providerOptions input:checked"))
    .map(input => parseInt(input.value, 10));

  try {
    await peticionJSON(`/api/eventos/${currentProviderEvent}/proveedores`, {
      method: "PUT",
      body: JSON.stringify({ proveedores: proveedorIds })
    });
    cerrarEditorProveedores();
  } catch (error) {
    alert("No se pudo guardar: " + error.message);
  }
}

function cerrarEditorProveedores() {
  document.getElementById("providerModule").style.display = "none";
  document.getElementById("eventList").style.display = "grid";
  document.getElementById("adminReturnArea").style.display = "block";
  renderEventList();
}

/* ========================
   CANCELAR / NAVEGACION
   ======================== */

function cancel() {
  document.getElementById("module").style.display = "none";
  document.getElementById("providerModule").style.display = "none";
  document.getElementById("eventList").style.display = "grid";
  document.getElementById("adminReturnArea").style.display = "block";
  renderEventList();
}

function volverAdministrador() {
  window.location.href = "/web/admin/";
}

window.addEventListener("DOMContentLoaded", cargarDatosIniciales);

/* ========================
   CERRAR SESIÓN
   ======================== */
async function cerrarSesion() {
  try {
    // 1. Llamar al endpoint del backend para destruir la sesión
    await peticionJSON("/api/logout", { method: "POST" });
    
    // 2. Redirigir al usuario a la página de login
    window.location.href = "/web/login/";
  } catch (error) {
    alert("Hubo un problema al cerrar la sesión: " + error.message);
    // Opcional: Forzar la redirección en caso de error de red
    window.location.href = "/web/login/";
  }
}

function alternarEvento() {
  // Ruta limpia definida en tu app.py para Booking (Rider)
  window.location.href = "/web/booking/"; 
}