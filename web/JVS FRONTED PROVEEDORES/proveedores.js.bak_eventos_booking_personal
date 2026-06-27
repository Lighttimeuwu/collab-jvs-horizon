let currentEvent = "";
let data = {};

/* ========================
   ABRIR MÓDULO
   ======================== */

function openModule(eventName) {
  currentEvent = eventName;

  if (!data[eventName]) {
    data[eventName] = {
      checks:   {},
      personal: []
    };
  }

  document.getElementById("eventTitle").innerText = "Evento: " + eventName;
  document.getElementById("module").style.display    = "block";
  document.getElementById("eventList").style.display = "none";

  render();
}

/* ========================
   RENDERIZAR CONTENIDO
   ======================== */

function render() {
  let d = data[currentEvent];

  document.getElementById("content").innerHTML = `
    <div class="section">
      <h4>Audio</h4>
      ${checkbox("Bocinas y Subwoofers")}
      ${checkbox("Consola de mezcla")}
      ${checkbox("Micrófonos")}
    </div>

    <div class="section">
      <h4>Iluminación Escénica</h4>
      ${checkbox("Luces LED y Wash")}
      ${checkbox("Cabezas móviles/Robóticas")}
      ${checkbox("Consola DMX")}
      ${checkbox("Máquina de humo")}
    </div>

    <div class="section">
      <h4>Video y Visuales</h4>
      ${checkbox("Pantallas LED")}
    </div>

    <div class="section">
      <h4>Estructura y Escenario</h4>
      ${checkbox("Escenario (Tarimas)")}
      ${checkbox("Trípodes y Stands")}
      ${checkbox("Cableado y conectividad")}
    </div>

    <div class="section">
      <h4>Personal Técnico</h4>
      <div id="personalList">
        ${d.personal.map(p => `<div>${p} <button onclick="removePerson('${p}')">X</button></div>`).join("")}
      </div>
      <input type="text" id="newPerson" placeholder="Agregar personal">
      <button onclick="addPerson()">Agregar</button>
    </div>
  `;
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
}

/* ========================
   PERSONAL TÉCNICO
   ======================== */

function addPerson() {
  let input = document.getElementById("newPerson");
  if (input.value.trim() !== "") {
    data[currentEvent].personal.push(input.value.trim());
    input.value = "";
    render();
  }
}

function removePerson(name) {
  data[currentEvent].personal = data[currentEvent].personal.filter(p => p !== name);
  render();
}

/* ========================
   GUARDAR / CANCELAR
   ======================== */

function save() {
  alert("Guardado exitosamente");
  cancel();
}

function cancel() {
  document.getElementById("module").style.display    = "none";
  document.getElementById("eventList").style.display = "grid";
}
