const API_USUARIOS_URL      = "/api/usuarios";
const API_ASIENTOS_OCUPADOS_URL = "/api/asientos-ocupados";

/* ========================
   SESIÓN (fuente de verdad: servidor, no localStorage)
   ======================== */

let usuarioSesionCache = null;

async function obtenerUsuarioSesion(forzarRecarga = false) {
  if (usuarioSesionCache && !forzarRecarga) return usuarioSesionCache;

  try {
    const respuesta = await fetch("/api/sesion", { credentials: "include" });
    const datos = await respuesta.json();

    if (!datos.ok || !datos.autenticado) {
      usuarioSesionCache = null;
      return null;
    }

    usuarioSesionCache = {
      nombre:   datos.nombre   || "",
      apellido: datos.apellido || "",
      correo:   (datos.correo  || "").trim(),
      cedula:   datos.cedula   || "",
      telefono: datos.telefono || "",
      rol_id:   datos.rol_id
    };
    return usuarioSesionCache;
  } catch (_) {
    return null;
  }
}

/* ========================
   NAVEGACIÓN ENTRE MÓDULOS
   ======================== */

function mostrar(id) {
  document.querySelectorAll(".modulo").forEach(m => m.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  if (id === "eventos") {
    renderCarteleraPublicada();
    cargarEventosAPI();
  }
  if (id === "mapa") {
    prepararMapaAsientos();
  }
}

async function cerrarSesion() {
  usuarioSesionCache = null;
  try {
    await fetch("/api/logout", {
      method: "POST",
      credentials: "include"
    });
  } catch (_) {}
  window.location.href = "/web/login/";
}

/* ========================
   GUARD: redirigir si no hay sesión + mensaje de bienvenida
   ======================== */
(async function verificarSesion() {
  const usuario = await obtenerUsuarioSesion();
  if (!usuario) {
    window.location.href = "/web/login/";
    return;
  }
  mostrarBienvenida(usuario);
})();

function mostrarBienvenida(usuario) {
  const contenedor = document.getElementById("bienvenidaUsuario");
  if (!contenedor) return;
  const nombre = usuario.nombre || "Usuario";
  contenedor.innerText = `Bienvenido, ${nombre}`;
}

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

function limpiarFecha(fecha = "") {
  return String(fecha).replace(/^\D*(?=\d)/, "").trim();
}

function obtenerJSON(clave) {
  return JSON.parse(localStorage.getItem(clave)) || [];
}

function formatearMoneda(valor) {
  return "$" + Number(valor || 0).toLocaleString("es-CO");
}

/* ========================
   CARTELERA PUBLICADA
   ======================== */

const detallesEventos = {
  "BAD BUNNY": {
    genero: "Reggaeton",
    lugar: "Bogotá",
    agenda: ["28 Marzo 2026 - Bogotá", "30 Abril 2026 - Medellín", "10 Agosto 2026 - Valledupar"],
    descripcionGeneral: "Bad Bunny es uno de los artistas mas influyentes de la musica urbana a nivel mundial; su estilo innovador y su impacto internacional lo han convertido en una referencia del genero. En esta presentacion los asistentes podran disfrutar de una noche llena de energia, produccion de primer nivel y sus mayores exitos en un espectaculo disenado para brindar una experiencia inolvidable."
  },
  "KAROL G": {
    genero: "Reggaeton / Urbano Latino",
    lugar: "Bogotá",
    agenda: ["01 Abril 2026 - Bogotá", "15 Septiembre 2026 - Huila", "27 Octubre 2026 - Medellín"],
    descripcionGeneral: "Karol G es una de las artistas latinas mas influyentes de la actualidad y una de las principales representantes de la musica urbana. En esta presentacion los asistentes podran disfrutar de una noche llena de energia, produccion de alto nivel y los temas mas importantes de su carrera en un espectaculo disenado para brindar una experiencia inolvidable."
  },
  "FEID": {
    genero: "Reggaeton",
    lugar: "Bogotá",
    agenda: ["20 Marzo 2026 - Bogotá", "25 Marzo 2026 - Medellín", "30 Marzo 2026 - Cali"],
    descripcionGeneral: "Feid se ha consolidado como uno de los maximos exponentes del reggaeton colombiano gracias a su estilo unico y su conexion con el publico. Esta presentacion reune sus exitos mas reconocidos en una experiencia pensada para miles de fanaticos, con energia, produccion profesional y una atmosfera cercana al universo del Ferxxo."
  },
  "ROMEO SANTOS": {
    genero: "Bachata",
    lugar: "Bogotá",
    agenda: ["25 Marzo 2026 - Bogotá", "15 Septiembre 2026 - Cali", "02 Octubre 2026 - Puerto Rico"],
    descripcionGeneral: "Romeo Santos es considerado uno de los maximos exponentes de la bachata a nivel mundial y una de las figuras mas importantes de la musica latina. Su show propone una noche llena de emociones, romanticismo y grandes exitos en un espectaculo creado para vivir una experiencia inolvidable."
  },
  "BASWELL": {
    genero: "Techno",
    lugar: "Bogotá",
    agenda: ["13 Abril 2026 - Bogotá", "31 Junio 2026 - Huila", "14 Octubre 2026 - Medellín"],
    descripcionGeneral: "Baswell es reconocido por sus presentaciones llenas de energia y su estilo caracteristico dentro de la escena techno internacional. Este evento rave ofrece una experiencia inmersiva de musica electronica con efectos visuales, sonido profesional y una atmosfera disenada para los amantes del techno."
  },
  "DOOM": {
    genero: "Hard Techno",
    lugar: "Bogotá",
    agenda: ["04 Abril 2026 - Bogotá", "14 Septiembre 2026 - Cali", "22 Octubre 2026 - Medellín"],
    descripcionGeneral: "Doom es un referente de la escena hard techno, reconocido por sus sesiones intensas y una puesta en escena de gran impacto. Esta noche esta dedicada a los sonidos mas potentes de la musica electronica, acompanados de una experiencia audiovisual compacta, oscura y contundente."
  }
};

let eventoActivoModal    = null;
let fechaSeleccionadaModal = "";
let compraActual         = null;

function normalizarNombreEvento(nombre = "") {
  const limpio = String(nombre).trim().toUpperCase();
  if (limpio.includes("BAD BUNNY")) return "BAD BUNNY";
  if (limpio.includes("KAROL"))     return "KAROL G";
  if (limpio.includes("FEID"))      return "FEID";
  if (limpio.includes("ROMEO"))     return "ROMEO SANTOS";
  if (limpio.includes("BASWELL") || limpio.includes("BASSWELL")) return "BASWELL";
  if (limpio.includes("DOOM"))      return "DOOM";
  return limpio;
}

function separarFechaLugar(fecha = "") {
  const partes     = String(fecha).split(" - ");
  const fechaTexto = limpiarFecha(partes[0] || fecha) || "Fecha no registrada";
  const lugar      = partes.length > 1 ? partes.slice(1).join(" - ").trim() : "";
  return { fecha: fechaTexto, lugar };
}

function formatearFechaOpcion(fecha = "") {
  const datos = separarFechaLugar(fecha);
  return datos.lugar ? `${datos.lugar} — ${datos.fecha}` : datos.fecha;
}

function obtenerDetalleEvento(evento) {
  const clave      = normalizarNombreEvento(evento.nombre || evento.clave || "");
  const detalle    = detallesEventos[clave] || {};
  const agendasBase = obtenerJSON("eventos_base_agenda");
  const agendaBase = agendasBase.find(item => item.id === evento.id || normalizarNombreEvento(item.nombre || "") === clave) || {};

  const fechasDisponibles = Array.isArray(agendaBase.fechas) && agendaBase.fechas.length
    ? agendaBase.fechas
    : (Array.isArray(evento.fechas) && evento.fechas.length
        ? evento.fechas
        : (detalle.agenda || []));

  const fechaBase  = fechasDisponibles[0] || evento.fecha || "";
  const fechaInfo  = separarFechaLugar(fechaBase);
  const imgFinal   = evento.imagen || evento.img || "";
  const horaFinal  = agendaBase.hora  || evento.hora  || detalle.hora  || "Hora no registrada";
  const lugarDePrimeraFecha = separarFechaLugar(fechaBase).lugar;
  const lugarFinal = lugarDePrimeraFecha || agendaBase.lugar || evento.lugar || detalle.lugar || "Ubicacion no registrada";
  const descripcionFinal = evento.descripcion || evento.descripcionGeneral || detalle.descripcionGeneral
    || "Este evento publicado en la cartelera de Focus Producciones combina una propuesta artistica destacada con produccion profesional, proveedores asignados y una experiencia preparada para el publico.";

  return {
    clave,
    id:                 evento.id || clave,
    nombre:             evento.nombre || "Evento",
    img:                imgFinal,
    genero:             detalle.genero || evento.tipo || "Evento musical",
    fecha:              fechaInfo.fecha,
    hora:               horaFinal,
    lugar:              lugarFinal,
    fechasDisponibles,
    descripcionGeneral: descripcionFinal
  };
}

function renderOpcionesFechaCompra(fechas = []) {
  const contenedor = document.getElementById("opcionesFechaCompra");
  if (!contenedor) return;

  const lista = fechas.length ? fechas : ["Fecha no registrada"];
  contenedor.innerHTML = lista.map(fecha => `
    <label class="event-date-option">
      <input type="radio" name="fechaCompraEvento" value="${escaparHTML(fecha)}">
      <span>${escaparHTML(formatearFechaOpcion(fecha))}</span>
    </label>
  `).join("");

  fechaSeleccionadaModal = "";
  contenedor.querySelectorAll('input[name="fechaCompraEvento"]').forEach(input => {
    input.addEventListener("change", function () {
      fechaSeleccionadaModal = this.value;
      const lugarDeFecha = separarFechaLugar(this.value).lugar;
      if (lugarDeFecha) {
        const elLugar = document.getElementById("modalEventoLugar");
        if (elLugar) elLugar.innerText = lugarDeFecha;
      }
    });
  });
}

function abrirModalEvento(evento) {
  const detalle = obtenerDetalleEvento(evento);
  const modal   = document.getElementById("modalEvento");

  const imgEl = document.getElementById("modalEventoImagen");
  imgEl.src = detalle.img || "";
  imgEl.alt = detalle.nombre;
  imgEl.onerror = function() {
    this.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400'%3E%3Crect width='600' height='400' fill='%23222'/%3E%3Ctext x='50%25' y='50%25' fill='%23666' font-size='18' text-anchor='middle' dy='.3em'%3ESin imagen%3C/text%3E%3C/svg%3E";
    this.onerror = null;
  };
  document.getElementById("modalEventoGenero").innerText   = detalle.genero;
  document.getElementById("modalEventoNombre").innerText   = detalle.nombre;
  document.getElementById("modalEventoHora").innerText     = detalle.hora;
  document.getElementById("modalEventoLugar").innerText    = detalle.lugar;
  document.getElementById("modalEventoDescripcionGeneral").innerText = detalle.descripcionGeneral;
  eventoActivoModal = detalle;

  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.body.classList.add("modal-open");
}

function cerrarModalEvento() {
  const modal = document.getElementById("modalEvento");
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
  cerrarModalSeleccionFecha();
  eventoActivoModal    = null;
  fechaSeleccionadaModal = "";
}

function abrirModalSeleccionFecha() {
  if (!eventoActivoModal) return;
  const modal = document.getElementById("modalSeleccionFecha");
  if (!modal) return;

  renderOpcionesFechaCompra(eventoActivoModal.fechasDisponibles || []);
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.body.classList.add("modal-open");
}

function cerrarModalSeleccionFecha() {
  const modal = document.getElementById("modalSeleccionFecha");
  if (!modal) return;
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
}

function comprarDesdeModal() {
  abrirModalSeleccionFecha();
}

function continuarCompraConFecha() {
  if (!fechaSeleccionadaModal) {
    alert("Debes seleccionar una fecha para continuar.");
    return;
  }

  const datosFecha = separarFechaLugar(fechaSeleccionadaModal);
  compraActual = {
    evento:     eventoActivoModal ? eventoActivoModal.nombre : "Evento",
    fecha:      fechaSeleccionadaModal,
    fechaTexto: datosFecha.fecha,
    lugar:      datosFecha.lugar || (eventoActivoModal ? eventoActivoModal.lugar : "")
  };
  localStorage.setItem("compra_evento_seleccionado", JSON.stringify(compraActual));

  cerrarModalSeleccionFecha();
  const modalEvento = document.getElementById("modalEvento");
  modalEvento.classList.remove("is-open");
  modalEvento.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
  eventoActivoModal    = null;
  fechaSeleccionadaModal = "";
  mostrar("mapa");
}

function verEventoBase(clave) {
  const tarjeta = document.querySelector(`[data-event-key="${clave}"]`);
  if (!tarjeta) return;

  abrirModalEvento({
    clave,
    id:     tarjeta.dataset.eventId || clave,
    nombre: tarjeta.querySelector("h3")?.innerText || clave,
    img:    tarjeta.querySelector("img")?.getAttribute("src") || ""
  });
}

function buscarEventoPublicado(id) {
  const idBuscado      = String(id);
  const cartelera      = obtenerCarteleraVigente();
  const desdeCartelera = cartelera.find(item => String(item.id) === idBuscado);
  if (desdeCartelera) return desdeCartelera;

  const eventosBooking  = obtenerJSON("eventos_publicados");
  const proveedoresData = JSON.parse(localStorage.getItem("proveedores_data") || "{}");
  const desdeBooking    = eventosBooking.find(item => String(item.id) === idBuscado);
  if (desdeBooking) {
    const gestion = proveedoresData[idBuscado] || {};
    return {
      id:          desdeBooking.id,
      nombre:      desdeBooking.nombre,
      img:         desdeBooking.imagen || desdeBooking.img,
      tipo:        desdeBooking.tipo || "Evento",
      lugar:       desdeBooking.lugar || separarFechaLugar((desdeBooking.fechas || [""])[0]).lugar,
      hora:        desdeBooking.hora || "",
      fechas:      desdeBooking.fechas || [],
      empresas:    gestion.empresas || [],
      personal:    gestion.personal || [],
      enCartelera: gestion.enCartelera === true
    };
  }
  return null;
}

function verEventoPublicado(id) {
  let evento = buscarEventoPublicado(id);

  if (String(id).startsWith("sqlite_")) {
    const apiId     = String(id).replace("sqlite_", "");
    const eventoAPI = eventosAPI.find(ev => String(ev.apiId) === String(apiId));
    if (eventoAPI) {
      evento = Object.assign({}, eventoAPI, {
        id:     id,
        img:    eventoAPI.img    || (evento && evento.imagen) || (evento && evento.img) || "",
        imagen: eventoAPI.imagen || (evento && evento.imagen) || ""
      });
    }
  }

  if (evento) { abrirModalEvento(evento); return; }
  alert("No se encontro la informacion del evento. Vuelve a enviarlo desde Proveedores a cartelera.");
}

window.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    const modalFecha = document.getElementById("modalSeleccionFecha");
    if (modalFecha && modalFecha.classList.contains("is-open")) cerrarModalSeleccionFecha();
    else cerrarModalEvento();
  }
});

function ocultarEventosBaseEliminados() {
  let eliminados = obtenerJSON("eventos_base_eliminados");
  document.querySelectorAll("[data-event-id]").forEach(tarjeta => {
    tarjeta.style.display = eliminados.includes(tarjeta.dataset.eventId) ? "none" : "";
  });
}

function obtenerEventosEnviadosDesdeProveedores() {
  let proveedoresData = JSON.parse(localStorage.getItem("proveedores_data") || "{}");
  let eventosBooking  = obtenerJSON("eventos_publicados");

  return eventosBooking
    .filter(evento => {
      let gestion = proveedoresData[evento.id];
      return gestion && gestion.enCartelera === true;
    })
    .map(evento => {
      let gestion = proveedoresData[evento.id] || {};
      return {
        id:          evento.id,
        nombre:      evento.nombre,
        img:         evento.imagen || evento.img,
        tipo:        evento.tipo || "Evento",
        lugar:       evento.lugar || separarFechaLugar((evento.fechas || [""])[0]).lugar,
        hora:        evento.hora || "",
        fechas:      evento.fechas || [],
        empresas:    gestion.empresas || [],
        personal:    gestion.personal || [],
        enCartelera: true
      };
    });
}

function unirCarteleraSinDuplicados(cartelera, enviados) {
  let mapa = new Map();
  cartelera.forEach(evento => mapa.set(evento.id, evento));
  enviados.forEach(evento => mapa.set(evento.id, Object.assign({}, mapa.get(evento.id) || {}, evento)));
  return Array.from(mapa.values());
}

function obtenerCarteleraVigente() {
  let cartelera           = obtenerJSON("cartelera_usuario");
  let eventosBooking      = obtenerJSON("eventos_publicados");
  let enviadosProveedores = obtenerEventosEnviadosDesdeProveedores();
  let carteleraUnida      = unirCarteleraSinDuplicados(cartelera, enviadosProveedores);

  const bookingPorId = {};
  eventosBooking.forEach(ev => { bookingPorId[ev.id] = ev; });

  carteleraUnida = carteleraUnida.map(evento => {
    const booking = bookingPorId[evento.id];
    if (!booking) return evento;
    return Object.assign({
      img:    booking.imagen || booking.img || evento.img || evento.imagen,
      imagen: booking.imagen || booking.img || evento.imagen || evento.img,
      hora:   booking.hora   || evento.hora,
      lugar:  booking.lugar  || evento.lugar,
      fechas: booking.fechas || evento.fechas,
      horas:  booking.horas  || evento.horas
    }, evento, {
      img:    booking.imagen || booking.img || evento.img || evento.imagen || "",
      imagen: booking.imagen || booking.img || evento.imagen || evento.img || ""
    });
  });

  let vigente = carteleraUnida.filter(evento => evento.enCartelera === true);
  localStorage.setItem("cartelera_usuario", JSON.stringify(vigente));
  return vigente;
}

function renderCarteleraPublicada() {
  let contenedor = document.getElementById("listaEventosUsuario");
  if (!contenedor) return;

  ocultarEventosBaseEliminados();
  contenedor.querySelectorAll(".evento-publicado").forEach(evento => evento.remove());
  let cartelera = obtenerCarteleraVigente();

  cartelera.forEach(evento => {
    const imgSrc   = evento.imagen || evento.img || "";
    const sqliteId = evento.sqliteId || (String(evento.id).startsWith("sqlite_") ? String(evento.id).replace("sqlite_", "") : "");
    const dataAttr = sqliteId ? `data-sqlite-id="${escaparHTML(sqliteId)}"` : "";
    contenedor.insertAdjacentHTML("beforeend", `
      <div class="evento evento-publicado" ${dataAttr}>
        <img src="${escaparHTML(imgSrc)}" alt="${escaparHTML(evento.nombre)}">
        <h3>${escaparHTML(evento.nombre)}</h3>
        <div class="event-card-actions">
          <button onclick="verEventoPublicado('${escaparHTML(evento.id)}')">Ver Evento</button>
        </div>
      </div>
    `);
  });
}

renderCarteleraPublicada();

window.addEventListener("storage", function (event) {
  if (["cartelera_usuario", "eventos_publicados", "proveedores_data", "eventos_base_eliminados", "eventos_base_agenda"].includes(event.key)) {
    renderCarteleraPublicada();
  }
});

/* ========================
   EVENTOS DESDE API
   ======================== */

let eventosAPI = [];

function normalizarEventoAPI(evento) {
  const funciones      = Array.isArray(evento.funciones) ? evento.funciones : [];
  const fechas         = funciones.map(funcion => {
    const fecha = funcion.fecha || evento.fecha || "Fecha no registrada";
    return funcion.lugar ? `${fecha} - ${funcion.lugar}` : fecha;
  });
  const primeraFuncion = funciones[0] || {};
  const imgReal = evento.imagen || evento.img || "";

  return {
    id:                 `api_${evento.id}`,
    apiId:              evento.id,
    nombre:             evento.nombre || "Evento",
    fecha:              evento.fecha  || primeraFuncion.fecha || "Fecha no registrada",
    hora:               primeraFuncion.hora  || evento.hora  || "Hora no registrada",
    lugar:              primeraFuncion.lugar || evento.lugar || "Ubicacion no registrada",
    fechas:             fechas.length ? fechas : [evento.fecha || "Fecha no registrada"],
    tipo:               "Evento SQLite",
    img:                imgReal,
    imagen:             imgReal,
    descripcion:        evento.descripcion || evento.Descripcion || "",
    descripcionGeneral: evento.descripcion || evento.Descripcion || "Evento cargado desde SQLite mediante Flask."
  };
}

async function cargarEventosAPI() {
  const contenedor = document.getElementById("listaEventosUsuario");
  if (!contenedor) return;

  // Pedir al servidor que despublique en la DB los eventos cuyas fechas ya pasaron.
  // Es silencioso: si falla (sin conexion, etc.) simplemente se omite.
  try {
    await fetch("/api/eventos/limpiar-vencidos", { method: "POST" });
  } catch (_) {}

  try {
    const respuesta = await fetch("/api/eventos?publicados=1");
    if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);

    const datos = await respuesta.json();
    if (!datos.ok || !Array.isArray(datos.eventos)) return;

    eventosAPI = datos.eventos.map(normalizarEventoAPI);

    const idsCarteleraPublicada = new Set(
      (JSON.parse(localStorage.getItem("cartelera_usuario") || "[]"))
        .map(ev => ev.id)
    );

    const proveedoresData = JSON.parse(localStorage.getItem("proveedores_data") || "{}");

    contenedor.querySelectorAll(".evento-api").forEach(ev => ev.remove());

    eventosAPI.forEach(evento => {
      const idSqlite = "sqlite_" + evento.apiId;
      // Los eventos de SQLite ya vienen filtrados por publicado=1 desde el servidor.
      // Solo ocultamos duplicados que ya están en la cartelera del localStorage.
      if (idsCarteleraPublicada.has(idSqlite) || idsCarteleraPublicada.has(evento.id)) return;

      const imgSrc = evento.img
        ? evento.img
        : "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='190'%3E%3Crect width='300' height='190' fill='%23333'/%3E%3Ctext x='50%25' y='50%25' fill='%23999' font-size='14' text-anchor='middle' dy='.3em'%3ESin imagen%3C/text%3E%3C/svg%3E";

      contenedor.insertAdjacentHTML("beforeend", `
        <div class="evento evento-api" data-event-id="${escaparHTML(evento.id)}">
          <img src="${escaparHTML(imgSrc)}" alt="${escaparHTML(evento.nombre)}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22190%22%3E%3Crect width=%22300%22 height=%22190%22 fill=%22%23333%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 fill=%22%23999%22 font-size=%2214%22 text-anchor=%22middle%22 dy=%22.3em%22%3ESin imagen%3C/text%3E%3C/svg%3E'">
          <h3>${escaparHTML(evento.nombre)}</h3>
          <div class="event-card-actions">
            <button onclick="verEventoAPI('${escaparHTML(evento.id)}')">Ver Evento</button>
          </div>
        </div>
      `);
    });

    eventosAPI.forEach(eventoAPI => {
      const tarjeta = contenedor.querySelector(`.evento-publicado[data-sqlite-id="${eventoAPI.apiId}"]`);
      if (tarjeta) {
        const img = tarjeta.querySelector("img");
        if (img && eventoAPI.img && eventoAPI.img !== "imagenes/doom.jpg.jpg") {
          img.src = eventoAPI.img;
        }
      }
    });

  } catch (error) {
    console.warn("No se pudieron cargar eventos desde Flask:", error);
  }
}

function verEventoAPI(id) {
  const evento = eventosAPI.find(item => item.id === id);
  if (evento) abrirModalEvento(evento);
}

cargarEventosAPI();

/* ========================
   ASIENTOS
   ======================== */

let seleccionados = [];
let ultimaCompra  = "";
let facturaActual = null;
const PRECIO_UNITARIO_BOLETA   = 85000;
const IVA_FACTURA              = 0.19;
const CLAVE_ASIENTOS_OCUPADOS  = "asientos_ocupados_eventos";

function obtenerClaveCompraAsientos() {
  const compra = obtenerCompraSeleccionada();
  const evento = compra.evento || "Evento";
  const fecha  = compra.fecha  || "Fecha no seleccionada";
  return `${evento}__${fecha}`.toLowerCase().replace(/\s+/g, "_");
}

function obtenerAsientosOcupados() {
  return JSON.parse(localStorage.getItem(CLAVE_ASIENTOS_OCUPADOS) || "{}");
}

function guardarAsientosOcupados(registro) {
  localStorage.setItem(CLAVE_ASIENTOS_OCUPADOS, JSON.stringify(registro));
}

function obtenerOcupadosCompraActual() {
  const registro = obtenerAsientosOcupados();
  return registro[obtenerClaveCompraAsientos()] || [];
}

function datosConsultaAsientos() {
  const compra = obtenerCompraSeleccionada();
  return {
    evento:     compra.evento    || "Evento",
    fecha:      compra.fecha     || "Fecha no seleccionada",
    evento_id:  compra.eventoId  || compra.apiId || "",
    funcion_id: compra.funcionId || ""
  };
}

async function consultarOcupadosSQLite() {
  const datos  = datosConsultaAsientos();
  const params = new URLSearchParams();
  Object.keys(datos).forEach(clave => { if (datos[clave]) params.append(clave, datos[clave]); });

  const respuesta = await fetch(`${API_ASIENTOS_OCUPADOS_URL}?${params.toString()}`);
  const resultado = await respuesta.json();
  if (!respuesta.ok || !resultado.ok) throw new Error(resultado.error || "No se pudieron consultar los asientos ocupados.");
  return resultado.asientos || [];
}

async function registrarOcupadosSQLite(asientos) {
  const datos     = datosConsultaAsientos();
  const respuesta = await fetch(API_ASIENTOS_OCUPADOS_URL, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(Object.assign({}, datos, { asientos }))
  });
  const resultado = await respuesta.json();
  if (!respuesta.ok || !resultado.ok) throw new Error(resultado.error || "No se pudieron registrar los asientos ocupados.");
  return resultado.asientos || [];
}

function nombreAsiento(codigo = "") {
  const partes = String(codigo).split("-");
  const zona   = partes[0] || "";
  const silla  = partes[1] || codigo;
  const nombresZona = { graderia1: "Graderia Izquierda", vip: "VIP", graderia2: "Graderia Derecha" };
  return `${nombresZona[zona] || zona} ${silla}`.trim();
}

function textoAsientosSeleccionados() {
  return seleccionados.map(nombreAsiento).join(", ");
}

function actualizarResumenAsientos() {
  const contador = document.getElementById("contadorAsientos");
  const total    = document.getElementById("totalBoletasAsientos");
  if (contador) contador.innerText = seleccionados.length;
  if (total)    total.innerText    = seleccionados.length;
}

function crearAsientos(zona) {
  let letras = ["A", "B", "C", "D"];
  let cont   = document.getElementById(zona);
  if (!cont) return;

  for (let l of letras) {
    for (let i = 1; i <= 5; i++) {
      let a          = document.createElement("button");
      const codigo   = `${zona}-${l}${i}`;
      a.type         = "button";
      a.className    = "asiento";
      a.dataset.asiento = codigo;
      a.innerText    = l + i;
      a.setAttribute("aria-label", `Asiento ${l}${i} ${zona}`);

      a.onclick = function () {
        if (this.classList.contains("ocupado")) return;
        this.classList.toggle("seleccionado");
        if (this.classList.contains("seleccionado")) {
          if (!seleccionados.includes(codigo)) seleccionados.push(codigo);
        } else {
          seleccionados = seleccionados.filter(x => x !== codigo);
        }
        actualizarResumenAsientos();
      };

      cont.appendChild(a);
    }
  }
}

function aplicarAsientosOcupados(ocupados) {
  document.querySelectorAll(".asiento").forEach(asiento => {
    asiento.classList.remove("seleccionado", "ocupado");
    asiento.disabled = false;
    asiento.title    = "Disponible";

    if (ocupados.includes(asiento.dataset.asiento)) {
      asiento.classList.add("ocupado");
      asiento.disabled = true;
      asiento.title    = "No disponible";
    }
  });
}

async function prepararMapaAsientos() {
  seleccionados = [];
  aplicarAsientosOcupados(obtenerOcupadosCompraActual());
  actualizarResumenAsientos();

  try {
    const ocupadosSQLite = await consultarOcupadosSQLite();
    const registro = obtenerAsientosOcupados();
    registro[obtenerClaveCompraAsientos()] = ocupadosSQLite;
    guardarAsientosOcupados(registro);
    aplicarAsientosOcupados(ocupadosSQLite);
    actualizarResumenAsientos();
  } catch (error) {
    console.warn(error.message || "No se pudieron cargar asientos desde SQLite.");
  }
}

async function bloquearAsientosComprados() {
  const comprados = seleccionados.slice();
  const registro  = obtenerAsientosOcupados();
  const clave     = obtenerClaveCompraAsientos();
  const actuales  = new Set(registro[clave] || []);
  comprados.forEach(asiento => actuales.add(asiento));
  registro[clave] = Array.from(actuales);
  guardarAsientosOcupados(registro);

  try {
    const ocupadosSQLite = await registrarOcupadosSQLite(comprados);
    registro[clave] = ocupadosSQLite;
    guardarAsientosOcupados(registro);
  } catch (error) {
    console.warn(error.message || "No se pudieron registrar asientos en SQLite.");
  }

  prepararMapaAsientos();
}

crearAsientos("graderia1");
crearAsientos("graderia2");
crearAsientos("vip");
actualizarResumenAsientos();

/* ========================
   PAGO
   ======================== */

function obtenerCompraSeleccionada() {
  const compraGuardada = compraActual || obtenerJSON("compra_evento_seleccionado");
  return Array.isArray(compraGuardada) ? {} : compraGuardada;
}

function calcularValoresCompra() {
  const cantidad = seleccionados.length;
  const subtotal = PRECIO_UNITARIO_BOLETA * cantidad;
  const iva      = Math.round(subtotal * IVA_FACTURA);
  const total    = subtotal + iva;
  return { precioUnitario: PRECIO_UNITARIO_BOLETA, cantidad, subtotal, iva, total };
}

function renderPasarelaPSE() {
  const compra      = obtenerCompraSeleccionada();
  const valores     = calcularValoresCompra();
  const fechaCompra = compra.fecha || "Fecha no seleccionada";
  const lugarCompra = compra.lugar || separarFechaLugar(fechaCompra).lugar || "Lugar no registrado";

  document.getElementById("pseResumenCompra").innerHTML = `
    <p><strong>Evento</strong><span>${escaparHTML(compra.evento || "Evento")}</span></p>
    <p><strong>Fecha seleccionada</strong><span>${escaparHTML(fechaCompra)}</span></p>
    <p><strong>Lugar</strong><span>${escaparHTML(lugarCompra)}</span></p>
    <p><strong>Asientos seleccionados</strong><span>${escaparHTML(textoAsientosSeleccionados())}</span></p>
    <p><strong>Cantidad de boletas</strong><span>${valores.cantidad}</span></p>
  `;

  document.getElementById("pseResumenValores").innerHTML = `
    <p><span>Precio unitario</span><strong>${formatearMoneda(valores.precioUnitario)}</strong></p>
    <p><span>Cantidad</span><strong>${valores.cantidad}</strong></p>
    <p><span>Subtotal</span><strong>${formatearMoneda(valores.subtotal)}</strong></p>
    <p><span>IVA 19%</span><strong>${formatearMoneda(valores.iva)}</strong></p>
    <p class="pse-total"><span>Total a pagar</span><strong>${formatearMoneda(valores.total)}</strong></p>
  `;
}

async function autocompletarDatosCompradorPSE() {
  const usuarioLogueado = await obtenerUsuarioSesion();
  if (!usuarioLogueado || !usuarioLogueado.correo) return;

  const campoNombre    = document.getElementById("pseNombre");
  const campoDocumento = document.getElementById("pseDocumento");
  const campoCorreo    = document.getElementById("pseCorreo");
  const campoTelefono  = document.getElementById("pseTelefono");
  const nombreCompleto = ((usuarioLogueado.nombre || "") + " " + (usuarioLogueado.apellido || "")).trim();
  const correoEsValido = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(usuarioLogueado.correo);

  if (campoNombre    && !campoNombre.value.trim()    && nombreCompleto)           { campoNombre.value    = nombreCompleto;        campoNombre.readOnly    = true; }
  if (campoDocumento && !campoDocumento.value.trim() && usuarioLogueado.cedula)   { campoDocumento.value = usuarioLogueado.cedula; campoDocumento.readOnly = true; }
  if (campoTelefono  && !campoTelefono.value.trim()  && usuarioLogueado.telefono) { campoTelefono.value  = usuarioLogueado.telefono; campoTelefono.readOnly = true; }

  if (campoCorreo && !campoCorreo.value.trim() && usuarioLogueado.correo) {
    campoCorreo.value = usuarioLogueado.correo;
    // Solo se bloquea el campo si el correo guardado tiene un formato valido.
    // Si el correo registrado esta mal (dato antiguo o mal capturado), se deja
    // editable para que el comprador pueda corregirlo en el momento del pago.
    campoCorreo.readOnly = correoEsValido;
    if (!correoEsValido) {
      campoCorreo.title = "El correo registrado en tu cuenta parece invalido. Corrigelo aqui para continuar.";
    }
  }
}

async function abrirPasarelaPSE() {
  if (seleccionados.length === 0) { alert("Seleccione asientos"); return; }

  const compra = obtenerCompraSeleccionada();
  if (!compra.fecha) {
    alert("Debes seleccionar una fecha antes de pagar.");
    mostrar("eventos");
    return;
  }

  renderPasarelaPSE();
  mostrar("pse");
  await autocompletarDatosCompradorPSE();
}

function obtenerDatosCompradorPSE() {
  return {
    nombre:    document.getElementById("pseNombre").value.trim(),
    documento: document.getElementById("pseDocumento").value.trim(),
    correo:    document.getElementById("pseCorreo").value.trim(),
    telefono:  document.getElementById("pseTelefono").value.trim()
  };
}

function validarDatosCompradorPSE(datos) {
  const correoNormalizado = (datos.correo || "").trim();
  const correoValido = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correoNormalizado);
  if (!datos.nombre || !datos.documento || !correoNormalizado || !datos.telefono) {
    alert("Completa todos los datos del comprador.");
    return false;
  }
  if (!correoValido) { alert("Ingresa un correo electronico valido."); return false; }
  return true;
}

function construirFacturaLocal(datosComprador) {
  const compra      = obtenerCompraSeleccionada();
  const valores     = calcularValoresCompra();
  const fechaCompra = compra.fecha || "Fecha no seleccionada";
  const lugarCompra = compra.lugar || separarFechaLugar(fechaCompra).lugar || "Lugar no registrado";

  return {
    numero:         "FAC-" + Date.now(),
    fechaEmision:   new Date().toLocaleString("es-CO"),
    estadoPago:     "Pagado",
    metodoPago:     "PSE",
    comprador:      datosComprador,
    evento:         compra.evento || "Evento",
    fechaEvento:    fechaCompra,
    lugar:          lugarCompra,
    asientos:       seleccionados.map(nombreAsiento),
    cantidad:       valores.cantidad,
    precioUnitario: valores.precioUnitario,
    subtotal:       valores.subtotal,
    iva:            valores.iva,
    total:          valores.total
  };
}

function construirTextoQRFactura(factura) {
  return [
    "FOCUS PRODUCCIONES",
    "Factura: "        + factura.numero,
    "Estado: "         + factura.estadoPago,
    "Metodo de pago: " + factura.metodoPago,
    "Comprador: "      + factura.comprador.nombre,
    "Documento: "      + factura.comprador.documento,
    "Correo: "         + factura.comprador.correo,
    "Telefono: "       + factura.comprador.telefono,
    "Evento: "         + factura.evento,
    "Fecha: "          + factura.fechaEvento,
    "Lugar: "          + factura.lugar,
    "Asientos: "       + factura.asientos.join(", "),
    "Cantidad: "       + factura.cantidad,
    "Subtotal: "       + formatearMoneda(factura.subtotal),
    "IVA: "            + formatearMoneda(factura.iva),
    "Total: "          + formatearMoneda(factura.total)
  ].join("\n");
}

async function confirmarPagoPSE() {
  const datosComprador = obtenerDatosCompradorPSE();
  if (!validarDatosCompradorPSE(datosComprador)) return;

  facturaActual = construirFacturaLocal(datosComprador);
  await bloquearAsientosComprados();
  localStorage.setItem("factura_actual", JSON.stringify(facturaActual));

  const compras = obtenerJSON("compras_locales");
  compras.push(facturaActual);
  localStorage.setItem("compras_locales", JSON.stringify(compras));

  const usuarioLogueado = await obtenerUsuarioSesion();
  try {
    await fetch("/api/ventas/web", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        usuario_correo: (usuarioLogueado && usuarioLogueado.correo) || datosComprador.correo,
        usuario_nombre: (((usuarioLogueado && usuarioLogueado.nombre) || datosComprador.nombre) + " " + ((usuarioLogueado && usuarioLogueado.apellido) || "")).trim(),
        evento:         facturaActual.evento,
        fecha_evento:   facturaActual.fechaEvento,
        lugar:          facturaActual.lugar,
        asientos:       facturaActual.asientos,
        cantidad:       facturaActual.cantidad,
        total:          facturaActual.total,
        fecha_compra:   facturaActual.fechaEmision
      })
    });
  } catch (e) {
    console.warn("No se pudo guardar la venta en BD:", e);
  }

  alert("Compra realizada con exito");

  ultimaCompra = construirTextoQRFactura(facturaActual);
  const qrSrc  = "https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=" + encodeURIComponent(ultimaCompra);

  const resumenCompra = `
    <article class="receipt-preview">
      <header class="receipt-hero">
        <div>
          <span class="receipt-system">HORIZON JVS</span>
          <h3>FACTURA ELECTR&Oacute;NICA</h3>
        </div>
        <span class="receipt-approved">COMPRA APROBADA &#9989;</span>
      </header>
      <section class="receipt-meta">
        <p><strong>N&uacute;mero de factura</strong><span>${escaparHTML(facturaActual.numero)}</span></p>
        <p><strong>Fecha de emisi&oacute;n</strong><span>${escaparHTML(facturaActual.fechaEmision)}</span></p>
      </section>
      <section class="receipt-card receipt-buyer">
        <span class="receipt-card-label">Comprador</span>
        <p><strong>Nombre</strong><span>${escaparHTML(facturaActual.comprador.nombre)}</span></p>
        <p><strong>Documento</strong><span>${escaparHTML(facturaActual.comprador.documento)}</span></p>
        <p><strong>Correo electr&oacute;nico</strong><span>${escaparHTML(facturaActual.comprador.correo)}</span></p>
        <p><strong>Tel&eacute;fono</strong><span>${escaparHTML(facturaActual.comprador.telefono)}</span></p>
      </section>
      <section class="receipt-card receipt-event">
        <span class="receipt-card-label">Evento</span>
        <p><strong>Nombre del evento</strong><span>${escaparHTML(facturaActual.evento)}</span></p>
        <p><strong>Fecha</strong><span>${escaparHTML(facturaActual.fechaEvento)}</span></p>
        <p><strong>Lugar</strong><span>${escaparHTML(facturaActual.lugar)}</span></p>
      </section>
      <section class="receipt-card receipt-payment">
        <span class="receipt-card-label">Pago</span>
        <p><strong>M&eacute;todo</strong><span>${escaparHTML(facturaActual.metodoPago)}</span></p>
        <p><strong>Estado</strong><span>${escaparHTML(facturaActual.estadoPago)}</span></p>
      </section>
      <section class="receipt-card receipt-detail">
        <span class="receipt-card-label">Detalle de compra</span>
        <div class="receipt-line"><span>Asientos seleccionados</span><strong>${escaparHTML(facturaActual.asientos.join(", "))}</strong></div>
        <div class="receipt-line"><span>Cantidad</span><strong>${facturaActual.cantidad}</strong></div>
        <div class="receipt-line"><span>Precio unitario</span><strong>${formatearMoneda(facturaActual.precioUnitario)}</strong></div>
        <div class="receipt-line"><span>Subtotal</span><strong>${formatearMoneda(facturaActual.subtotal)}</strong></div>
        <div class="receipt-line"><span>IVA</span><strong>${formatearMoneda(facturaActual.iva)}</strong></div>
      </section>
      <section class="receipt-total-card">
        <span>TOTAL PAGADO</span>
        <strong>${formatearMoneda(facturaActual.total)}</strong>
      </section>
      <section class="receipt-qr">
        <span>PASE DE INGRESO</span>
        <img id="qrFactura" src="${qrSrc}" alt="Codigo QR de la factura">
        <p>Presenta este c&oacute;digo en el acceso al evento</p>
      </section>
    </article>
  `;

  document.getElementById("lista").innerHTML = resumenCompra;
  document.getElementById("qr").src = qrSrc;
  mostrar("resultado");
}

/* ========================
   DESCARGAR PDF
   ======================== */

function descargarPDF() {
  const qr      = document.getElementById("qr").src;
  const factura = facturaActual || JSON.parse(localStorage.getItem("factura_actual") || "null");

  if (!qr || !factura) { alert("Primero realiza una compra para generar la factura."); return; }
  if (!window.jspdf || !window.jspdf.jsPDF) { alert("No se pudo cargar el generador de PDF. Revisa tu conexion a internet e intenta de nuevo."); return; }

  fetch(qr)
    .then(respuesta => respuesta.blob())
    .then(blob => new Promise(resolve => {
      let lector = new FileReader();
      lector.onloadend = () => resolve(lector.result);
      lector.readAsDataURL(blob);
    }))
    .then(qrBase64 => {
      const { jsPDF } = window.jspdf;
      const pdf    = new jsPDF();
      const rojo   = [122, 0, 24];
      const fucsia = [255, 0, 77];
      const gris   = [75, 75, 75];

      function texto(label, valor, x, y, ancho = 76) {
        pdf.setFont("helvetica", "bold");
        pdf.setTextColor(...rojo);
        pdf.setFontSize(9);
        pdf.text(label, x, y);
        pdf.setFont("helvetica", "normal");
        pdf.setTextColor(25, 25, 25);
        pdf.setFontSize(10);
        const lineas = pdf.splitTextToSize(String(valor || "No registrado"), ancho);
        pdf.text(lineas, x, y + 5);
        return y + 8 + (lineas.length * 5);
      }

      pdf.setFillColor(8, 8, 8);
      pdf.rect(0, 0, 210, 34, "F");
      pdf.setFillColor(...rojo);
      pdf.rect(0, 30, 210, 4, "F");
      pdf.setTextColor(255, 255, 255);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(21);
      pdf.text("Focus Producciones", 16, 16);
      pdf.setFontSize(10);
      pdf.setTextColor(255, 210, 220);
      pdf.text("Factura / Entrada digital", 16, 25);

      pdf.setFillColor(255, 255, 255);
      pdf.setDrawColor(...rojo);
      pdf.roundedRect(14, 44, 182, 218, 5, 5, "S");

      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(...rojo);
      pdf.setFontSize(16);
      pdf.text("Factura preparada", 24, 58);
      pdf.setFontSize(9);
      pdf.setTextColor(...gris);
      pdf.text("No. " + factura.numero, 24, 66);
      pdf.text("Emitida: " + factura.fechaEmision, 112, 66);

      pdf.setDrawColor(235, 235, 235);
      pdf.line(24, 74, 186, 74);

      pdf.setFillColor(250, 244, 246);
      pdf.roundedRect(24, 82, 78, 58, 4, 4, "F");
      pdf.roundedRect(108, 82, 78, 58, 4, 4, "F");

      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(...rojo);
      pdf.setFontSize(11);
      pdf.text("Comprador", 30, 94);
      let yComprador = 102;
      yComprador = texto("Nombre",    factura.comprador.nombre,    30, yComprador, 62);
      yComprador = texto("Documento", factura.comprador.documento, 30, yComprador, 62);
      texto("Correo", factura.comprador.correo, 30, yComprador, 62);

      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(...rojo);
      pdf.setFontSize(11);
      pdf.text("Evento", 114, 94);
      let yEvento = 102;
      yEvento = texto("Nombre", factura.evento,      114, yEvento, 62);
      yEvento = texto("Fecha",  factura.fechaEvento, 114, yEvento, 62);
      texto("Lugar", factura.lugar, 114, yEvento, 62);

      pdf.setFillColor(13, 13, 13);
      pdf.roundedRect(24, 150, 162, 42, 4, 4, "F");
      pdf.setTextColor(255, 255, 255);
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(11);
      pdf.text("Detalle de compra", 32, 162);
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(10);
      pdf.text("Asientos: " + factura.asientos.join(", "), 32, 172);
      pdf.text("Cantidad: " + factura.cantidad + " boleta(s)", 32, 181);
      pdf.setTextColor(255, 175, 195);
      pdf.text("Metodo de pago: " + factura.metodoPago + "  |  Estado: " + factura.estadoPago, 32, 189);

      pdf.setFillColor(250, 244, 246);
      pdf.roundedRect(24, 202, 86, 58, 4, 4, "F");
      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(...rojo);
      pdf.setFontSize(11);
      pdf.text("Resumen economico", 32, 215);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(25, 25, 25);
      pdf.setFontSize(10);
      pdf.text("Precio unitario: " + formatearMoneda(factura.precioUnitario), 32, 226);
      pdf.text("Subtotal: "        + formatearMoneda(factura.subtotal),       32, 235);
      pdf.text("IVA: "             + formatearMoneda(factura.iva),            32, 244);
      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(...fucsia);
      pdf.setFontSize(13);
      pdf.text("Total: " + formatearMoneda(factura.total), 32, 255);

      pdf.setDrawColor(...rojo);
      pdf.roundedRect(122, 202, 64, 58, 4, 4, "S");
      pdf.addImage(qrBase64, "PNG", 132, 207, 44, 44);
      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(...rojo);
      pdf.setFontSize(8);
      pdf.text("QR de ingreso", 154, 256, { align: "center" });

      pdf.setFillColor(...rojo);
      pdf.rect(0, 282, 210, 15, "F");
      pdf.setTextColor(255, 255, 255);
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(9);
      pdf.text("Presenta esta factura y el codigo QR al ingresar al evento.", 105, 291, { align: "center" });

      pdf.save("factura-focus-producciones.pdf");
    })
    .catch(() => { alert("No se pudo generar el PDF. Intenta nuevamente."); });
}

/* ========================
   MIS ENTRADAS
   ======================== */

function construirTextoQRVenta(venta, usuario) {
  return [
    "FOCUS PRODUCCIONES",
    "Comprador: "  + (((usuario.nombre || "") + " " + (usuario.apellido || "")).trim() || "Cliente"),
    "Correo: "     + (usuario.correo || ""),
    "Evento: "     + (venta.evento || ""),
    "Fecha: "      + (venta.fecha_evento || ""),
    "Lugar: "      + (venta.lugar || ""),
    "Asientos: "   + (venta.asientos || ""),
    "Cantidad: "   + (venta.cantidad || ""),
    "Total: "      + formatearMoneda(venta.total),
    "Fecha de compra: " + (venta.fecha_compra || "")
  ].join("\n");
}

function obtenerQRSrcVenta(venta, usuario) {
  const texto = construirTextoQRVenta(venta, usuario);
  return "https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=" + encodeURIComponent(texto);
}

async function cargarMisEntradas() {
  const usuario    = await obtenerUsuarioSesion();
  const correo     = (usuario && usuario.correo) || "";
  const contenedor = document.getElementById("misEntradasLista");
  if (!contenedor) return;

  if (!correo) {
    contenedor.innerHTML = "<p>Debes iniciar sesion para ver tus entradas.</p>";
    return;
  }

  contenedor.innerHTML = "<p>Cargando entradas...</p>";

  try {
    const respuesta = await fetch(`/api/ventas/usuario/${encodeURIComponent(correo)}`);
    const datos     = await respuesta.json();

    if (!datos.ok || datos.ventas.length === 0) {
      contenedor.innerHTML = "<p>No tienes entradas compradas aun.</p>";
      return;
    }

    contenedor.innerHTML = datos.ventas.map(venta => `
      <div class="entrada-card">
        <div class="entrada-card__info">
          <h3>${escaparHTML(venta.evento)}</h3>
          <p><strong>Fecha del evento:</strong> ${escaparHTML(venta.fecha_evento)}</p>
          <p><strong>Lugar:</strong> ${escaparHTML(venta.lugar)}</p>
          <p><strong>Asientos:</strong> ${escaparHTML(venta.asientos)}</p>
          <p><strong>Cantidad:</strong> ${venta.cantidad} boleta(s)</p>
          <p><strong>Total pagado:</strong> ${formatearMoneda(venta.total)}</p>
          <p><strong>Fecha de compra:</strong> ${escaparHTML(venta.fecha_compra)}</p>
        </div>
        <div class="entrada-card__qr">
          <img src="${obtenerQRSrcVenta(venta, usuario)}" alt="Codigo QR de ingreso">
          <span>Pase de ingreso</span>
        </div>
      </div>
    `).join("");
  } catch (error) {
    contenedor.innerHTML = "<p>Error al cargar tus entradas. Verifica tu conexion.</p>";
  }
}