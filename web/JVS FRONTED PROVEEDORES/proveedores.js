/* ========================
   ESTADO
   ======================== */

let eventos = [];                  // cache de GET /api/eventos
let catalogoProveedores = [];       // cache de GET /api/proveedores
let currentEvent = null;            // Evento_Id (numero) del modulo de personal abierto
let currentEventName = "";
let currentProviderEvent = null;    // Evento_Id (numero) del editor de proveedores abierto

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

function escaparJS(valor = "") {
  return String(valor).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
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
    const [datosEventos, datosProveedores] = await Promise.all([
      peticionJSON("/api/eventos"),
      peticionJSON("/api/proveedores")
    ]);
    eventos = datosEventos.eventos || [];
    catalogoProveedores = datosProveedores.proveedores || [];
    renderEventList();
  } catch (error) {
    const contenedor = document.getElementById("eventList");
    contenedor.innerHTML = `<p class="provider-empty">No se pudieron cargar los eventos: ${escaparHTML(error.message)}</p>`;
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

  contenedor.innerHTML = eventos.map(evento => `
    <div class="event" onclick="openModule(${evento.id}, '${escaparJS(evento.nombre)}')">
      <img src="${escaparHTML(evento.imagen || '')}" alt="${escaparHTML(evento.nombre)}">
      <h3>${escaparHTML(evento.nombre)}</h3>
      ${evento.lugar ? `<p class="event-place">${escaparHTML(evento.lugar)}</p>` : ""}
      <div id="empresas-evento-${evento.id}" class="provider-tags-wrapper">Cargando proveedores...</div>
      ${evento.publicado
        ? `<p class="sent-board-status">Publicado en cartelera</p>`
        : ""}
      <div class="event-actions">
        <button class="provider-card-btn" onclick="abrirEditorProveedores(event, ${evento.id}, '${escaparJS(evento.nombre)}')">Asignar proveedores</button>
      </div>
    </div>
  `).join("");

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
  const publicado = evento ? evento.publicado : false;

  document.getElementById("content").innerHTML = `
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

  await cargarYRenderPersonal();
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