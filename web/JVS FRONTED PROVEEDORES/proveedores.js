let currentEvent = "";
let currentEventName = "";
let currentProviderEvent = "";
let data = JSON.parse(localStorage.getItem("proveedores_data")) || {};

const empresasProveedoras = [
  "NovaTech Solutions",
  "Grupo Altiora",
  "Impulsa Global",
  "Vertex Consulting",
  "InnovaMax"
];

const eventosBase = [
  { id: "Feid", nombre: "Feid", img: "imagenes/feid.jpg.jpeg", tipo: "Concierto", fechas: ["10/08/2026"] },
  { id: "Karol G", nombre: "Karol G", img: "imagenes/karolg.jpeg.jpeg", tipo: "Concierto", fechas: ["12/08/2026"] },
  { id: "Doom", nombre: "Doom", img: "imagenes/doom.jpg.jpg", tipo: "Festivales", fechas: ["15/08/2026"] },
  { id: "Bad Bunny", nombre: "Bad Bunny", img: "imagenes/badbunny.jpg.jpeg", tipo: "Concierto", fechas: ["20/08/2026"] },
  { id: "Basswell", nombre: "Basswell", img: "imagenes/baswell.jpg.jpg", tipo: "Pool Party", fechas: ["25/08/2026"] },
  { id: "Romeo Santos", nombre: "Romeo Santos", img: "imagenes/romeo.jpg.jpg", tipo: "Concierto", fechas: ["30/08/2026"] }
];

function guardarDatos() {
  localStorage.setItem("proveedores_data", JSON.stringify(data));
}

function obtenerLugarDesdeFechas(fechas = []) {
  if (!Array.isArray(fechas) || !fechas.length) return "";
  const partes = String(fechas[0]).split(" - ");
  return partes.length > 1 ? partes.slice(1).join(" - ").trim() : "";
}

function obtenerEventosBooking() {
  return (JSON.parse(localStorage.getItem("eventos_publicados")) || []).map(evento => ({
    id: evento.id,
    nombre: evento.nombre,
    img: evento.imagen,
    tipo: evento.tipo || "",
    lugar: evento.lugar || obtenerLugarDesdeFechas(evento.fechas),
    hora: evento.hora || "",
    fechas: evento.fechas || []
  }));
}

function obtenerTodosEventosProveedor() {
  return eventosBase.concat(obtenerEventosBooking());
}

function esEventoBase(id) {
  return eventosBase.some(evento => evento.id === id);
}

function asegurarEvento(eventId) {
  if (!data[eventId]) {
    data[eventId] = {
      checks: {},
      personal: [],
      empresas: []
    };
  }

  if (!data[eventId].checks) data[eventId].checks = {};
  if (!Array.isArray(data[eventId].personal)) data[eventId].personal = [];
  if (!Array.isArray(data[eventId].empresas)) data[eventId].empresas = [];
}

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

function renderEmpresasEvento(eventId) {
  asegurarEvento(eventId);
  const empresas = data[eventId].empresas;

  if (!empresas.length) {
    return `<p class="provider-empty">Sin proveedor asignado</p>`;
  }

  return `
    <div class="provider-tags">
      ${empresas.map(empresa => `<span>${escaparHTML(empresa)}</span>`).join("")}
    </div>
  `;
}

function eventoListoParaCartelera(eventId) {
  asegurarEvento(eventId);
  return data[eventId].empresas.length > 0 && data[eventId].personal.length > 0;
}

function eventoEnCartelera(id) {
  if (data[id] && data[id].enCartelera === true) return true;
  return (JSON.parse(localStorage.getItem("cartelera_usuario")) || [])
    .some(evento => evento.id === id);
}

function renderEventList() {
  const contenedor = document.getElementById("eventList");
  const eventos = obtenerTodosEventosProveedor();

  contenedor.innerHTML = eventos.map(evento => `
    <div class="event" onclick="openModule('${escaparJS(evento.id)}', '${escaparJS(evento.nombre)}')">
      <img src="${escaparHTML(evento.img)}" alt="${escaparHTML(evento.nombre)}">
      <h3>${escaparHTML(evento.nombre)}</h3>
      ${evento.tipo ? `<p class="event-type">${escaparHTML(evento.tipo)}</p>` : ""}
      ${renderEmpresasEvento(evento.id)}
      ${(esEventoBase(evento.id) || eventoEnCartelera(evento.id)) ? `<p class="sent-board-status">Enviado a cartelera</p>` : ""}
      <div class="event-actions">
        <button class="provider-card-btn" onclick="abrirEditorProveedores(event, '${escaparJS(evento.id)}', '${escaparJS(evento.nombre)}')">Agregar proveedor</button>
      </div>
    </div>
  `).join("");
}

function mandarACartelera(eventId) {
  asegurarEvento(eventId);

  if (esEventoBase(eventId)) {
    alert("Este evento ya esta enviado a cartelera.");
    return;
  }

  if (!eventoListoParaCartelera(eventId)) {
    alert("Primero asigna al menos un proveedor y una persona de personal.");
    return;
  }

  const evento = obtenerTodosEventosProveedor().find(item => item.id === eventId);
  if (!evento) return;

  const cartelera = JSON.parse(localStorage.getItem("cartelera_usuario")) || [];
  const publicado = {
    id: evento.id,
    nombre: evento.nombre,
    img: evento.img,
    tipo: evento.tipo || "Evento",
    lugar: evento.lugar || obtenerLugarDesdeFechas(evento.fechas),
    hora: evento.hora || "",
    fechas: evento.fechas || [],
    empresas: data[eventId].empresas,
    personal: data[eventId].personal,
    enCartelera: true
  };

  const actualizada = cartelera.filter(item => item.id !== eventId);
  actualizada.push(publicado);
  data[eventId].enCartelera = true;
  guardarDatos();
  localStorage.setItem("cartelera_usuario", JSON.stringify(actualizada));
  alert("Evento enviado a la cartelera de usuario.");
  renderEventList();
}

function mandarACarteleraDesdeModulo() {
  mandarACartelera(currentEvent);
  render();
}

/* ========================
   ABRIR MODULO
   ======================== */

function openModule(eventId, eventName = eventId) {
  currentEvent = eventId;
  currentEventName = eventName;
  asegurarEvento(eventId);

  document.getElementById("eventTitle").innerText = "Evento: " + eventName;
  document.getElementById("module").style.display = "block";
  document.getElementById("providerModule").style.display = "none";
  document.getElementById("eventList").style.display = "none";
  document.getElementById("adminReturnArea").style.display = "none";

  render();
}

function abrirEditorProveedores(eventoClick, eventId, eventName) {
  eventoClick.stopPropagation();
  currentProviderEvent = eventId;
  asegurarEvento(eventId);

  document.getElementById("providerTitle").innerText = "Proveedores: " + eventName;
  document.getElementById("eventList").style.display = "none";
  document.getElementById("adminReturnArea").style.display = "none";
  document.getElementById("module").style.display = "none";
  document.getElementById("providerModule").style.display = "block";
  renderOpcionesEmpresas();
}

function renderOpcionesEmpresas() {
  const seleccionadas = data[currentProviderEvent].empresas;
  document.getElementById("providerOptions").innerHTML = empresasProveedoras.map(empresa => {
    const checked = seleccionadas.includes(empresa) ? "checked" : "";
    return `
      <label class="provider-option">
        <input type="checkbox" value="${escaparHTML(empresa)}" ${checked}>
        <span>${escaparHTML(empresa)}</span>
      </label>
    `;
  }).join("");
}

function guardarEmpresasEvento() {
  data[currentProviderEvent].empresas = Array.from(document.querySelectorAll("#providerOptions input:checked"))
    .map(input => input.value);
  guardarDatos();
  cerrarEditorProveedores();
}

function cerrarEditorProveedores() {
  document.getElementById("providerModule").style.display = "none";
  document.getElementById("eventList").style.display = "grid";
  document.getElementById("adminReturnArea").style.display = "block";
  renderEventList();
}

/* ========================
   RENDERIZAR CONTENIDO
   ======================== */

function render() {
  let d = data[currentEvent];
  const listoCartelera = eventoListoParaCartelera(currentEvent);
  const enviadoCartelera = esEventoBase(currentEvent) || eventoEnCartelera(currentEvent);

  document.getElementById("content").innerHTML = `
    <div class="section">
      <h4>Audio</h4>
      ${checkbox("Bocinas y Subwoofers")}
      ${checkbox("Consola de mezcla")}
      ${checkbox("Microfonos")}
    </div>

    <div class="section">
      <h4>Iluminacion Escenica</h4>
      ${checkbox("Luces LED y Wash")}
      ${checkbox("Cabezas moviles/Roboticas")}
      ${checkbox("Consola DMX")}
      ${checkbox("Maquina de humo")}
    </div>

    <div class="section">
      <h4>Video y Visuales</h4>
      ${checkbox("Pantallas LED")}
    </div>

    <div class="section">
      <h4>Estructura y Escenario</h4>
      ${checkbox("Escenario (Tarimas)")}
      ${checkbox("Tripodes y Stands")}
      ${checkbox("Cableado y conectividad")}
    </div>

    <div class="section">
      <h4>Personal Tecnico</h4>
      <p class="helper-text">Selecciona funciones arriba y luego agrega el nombre del personal.</p>
      <div id="personalList">
        ${renderPersonal(d.personal)}
      </div>
      <input type="text" id="newPerson" placeholder="Agregar personal">
      <button onclick="addPerson()">Agregar</button>
    </div>

    <div class="module-board-actions">
      ${enviadoCartelera
        ? `<p class="sent-board-status in-module">Enviado a cartelera</p>`
        : `<button class="send-board-btn" onclick="mandarACarteleraDesdeModulo()" ${listoCartelera ? "" : "disabled"}>Mandar a cartelera</button>`}
    </div>
  `;
}

function renderPersonal(personal) {
  if (!personal.length) return `<p class="empty-personal">No hay personal asignado.</p>`;

  return personal.map((persona, index) => {
    const normalizada = typeof persona === "string"
      ? { nombre: persona, funciones: [] }
      : persona;
    const funciones = normalizada.funciones && normalizada.funciones.length
      ? normalizada.funciones.map(f => `<span>${f}</span>`).join("")
      : `<em>Sin funciones seleccionadas</em>`;

    return `
      <div class="personal-item">
        <div>
          <b>${normalizada.nombre}</b>
          <div class="funciones-personal">${funciones}</div>
        </div>
        <button onclick="removePerson(${index})">X</button>
      </div>
    `;
  }).join("");
}

/* ========================
   CHECKBOX
   ======================== */

function checkbox(name) {
  let checked = data[currentEvent].checks[name] ? "checked" : "";
  return `<label><input type="checkbox" ${checked} onchange="toggle('${name}', this.checked)"> ${name}</label><br>`;
}

function toggle(name, value) {
  data[currentEvent].checks[name] = value;
  guardarDatos();
}

function obtenerFuncionesSeleccionadas() {
  return Object.entries(data[currentEvent].checks)
    .filter(([, activo]) => activo)
    .map(([nombre]) => nombre);
}

/* ========================
   PERSONAL TECNICO
   ======================== */

function addPerson() {
  let input = document.getElementById("newPerson");
  const nombre = input.value.trim();
  if (nombre === "") return;

  data[currentEvent].personal.push({
    nombre,
    funciones: obtenerFuncionesSeleccionadas()
  });

  input.value = "";
  guardarDatos();
  render();
}

function removePerson(index) {
  data[currentEvent].personal.splice(index, 1);
  guardarDatos();
  render();
}

/* ========================
   GUARDAR / CANCELAR
   ======================== */

function save() {
  guardarDatos();
  alert("Guardado exitosamente");
  cancel();
}

function cancel() {
  document.getElementById("module").style.display = "none";
  document.getElementById("providerModule").style.display = "none";
  document.getElementById("eventList").style.display = "grid";
  document.getElementById("adminReturnArea").style.display = "block";
  renderEventList();
}

function volverAdministrador() {
  localStorage.setItem("admin_entrar_menu", "true");
  window.location.href = "../JVS FRONTED ADMINISTRADOR/index.html";
}

window.addEventListener("DOMContentLoaded", renderEventList);
window.addEventListener("storage", function(event) {
  if (event.key === "eventos_publicados" || event.key === "cartelera_usuario") renderEventList();
});
