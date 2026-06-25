let artistaIdActual = "";
let riderFiltroActual = null;
const API_EVENTOS_URL = 'http://127.0.0.1:5000/api/eventos';
const API_RIDERS_URL = 'http://127.0.0.1:5000/api/riders';
function urlActualizarEventoSQLite(id) { return API_EVENTOS_URL + '/' + id; }
function urlRider(artistaId) { return API_RIDERS_URL + '/' + encodeURIComponent(artistaId); }
const IMAGEN_EVENTO_SQLITE = 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?auto=format&fit=crop&w=900&q=80';

const EVENTOS_BASE = [
    { id: 'art1', n: 'Feid' },
    { id: 'art2', n: 'Bad Bunny' },
    { id: 'art3', n: 'Romeo Santos' },
    { id: 'art4', n: 'Evento Techno' },
    { id: 'art5', n: 'Karol G' },
    { id: 'art6', n: 'Evento Rave' }
];

const LOCALIDADES_EVENTO = [
    'Movistar Arena',
    'Hotel Paradise',
    'Pradera Box',
    'Club Campestre',
    'Trisquel Bar',
    'Aurora Discoteca',
    'Plaza mayor',
    'Finca Villa Sol',
    'Parque Simon Bolivar',
    'Vintage Disco'
];

function obtenerEventosPublicados() {
    return JSON.parse(localStorage.getItem('eventos_publicados')) || [];
}
function esEventoSQLite(evento) {
    return evento && evento.origen === 'sqlite';
}

function normalizarFechaSQLite(fecha = '') {
    if (!fecha) return 'Fecha por definir';
    if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) return fecha;
    return formatearFechaEvento(fecha);
}

function crearEventoBookingDesdeAPI(evento) {
    const funciones = Array.isArray(evento.funciones) ? evento.funciones : [];
    const primeraFuncion = funciones[0] || {};
    const lugar = evento.lugar || primeraFuncion.lugar || 'Movistar Arena';
    const fechas = funciones.length
        ? funciones.map(funcion => `${normalizarFechaSQLite(funcion.fecha || evento.fecha)} - ${funcion.lugar || lugar}`)
        : [`${normalizarFechaSQLite(evento.fecha)} - ${lugar}`];
    const horaBase = primeraFuncion.hora || evento.hora || '08:00 PM';

    return {
        id: 'sqlite_' + evento.id,
        sqliteId: evento.id,
        origen: 'sqlite',
        nombre: evento.nombre || 'Evento SQLite',
        tipo: evento.tipo || 'Evento SQLite',
        descripcion: evento.descripcion || evento.Descripcion || '',
        lugar: lugar,
        hora: horaBase,
        horas: funciones.length ? funciones.map(funcion => funcion.hora || horaBase) : [horaBase],
        fechas: fechas,
        imagen: evento.imagen || IMAGEN_EVENTO_SQLITE
    };
}

async function cargarEventosDesdeAPI() {
    try {
        const respuesta = await fetch(API_EVENTOS_URL);
        if (!respuesta.ok) throw new Error('HTTP ' + respuesta.status);

        const datos = await respuesta.json();
        const eventosAPI = Array.isArray(datos) ? datos : (Array.isArray(datos.eventos) ? datos.eventos : []);
        if (eventosAPI.length === 0) return;

        const eventosActuales = obtenerEventosPublicados();
        let huboCambios = false;

        eventosAPI.forEach(eventoAPI => {
            const eventoBooking = crearEventoBookingDesdeAPI(eventoAPI);
            const indice = eventosActuales.findIndex(evento => evento.id === eventoBooking.id);
            if (indice >= 0) {
                eventosActuales[indice] = Object.assign({}, eventosActuales[indice], eventoBooking);
                huboCambios = true;
            } else {
                eventosActuales.push(eventoBooking);
                huboCambios = true;
            }
        });

        if (huboCambios) guardarEventosPublicados(eventosActuales);
        renderEventosPublicados();
        actualizarSelectRider();
        actualizarTablaRider();
    } catch (error) {
        console.warn('No se pudieron cargar eventos desde SQLite/Flask:', error);
    }
}

function obtenerEventosBaseEliminados() {
    return JSON.parse(localStorage.getItem('eventos_base_eliminados')) || [];
}

function guardarEventosBaseEliminados(eventos) {
    localStorage.setItem('eventos_base_eliminados', JSON.stringify(eventos));
}

function obtenerEventosBaseVisibles() {
    const eliminados = obtenerEventosBaseEliminados();
    return EVENTOS_BASE.filter(evento => !eliminados.includes(evento.id));
}

function guardarEventosPublicados(eventos) {
    try {
        localStorage.setItem('eventos_publicados', JSON.stringify(eventos));
    } catch (err) {
        // Cuota de localStorage excedida: limpiar imágenes base64 pesadas y reintentar
        console.warn('localStorage lleno, eliminando imágenes base64 y reintentando...');
        const limpios = eventos.map(ev => {
            if (ev.imagen && ev.imagen.startsWith('data:')) {
                return Object.assign({}, ev, { imagen: IMAGEN_EVENTO_SQLITE });
            }
            return ev;
        });
        try {
            localStorage.setItem('eventos_publicados', JSON.stringify(limpios));
        } catch (err2) {
            console.error('No se pudo guardar eventos_publicados ni tras limpiar:', err2);
        }
    }
}

function eliminarEventoVistaUsuario(id) {
    const cartelera = JSON.parse(localStorage.getItem('cartelera_usuario')) || [];
    localStorage.setItem('cartelera_usuario', JSON.stringify(cartelera.filter(evento => evento.id !== id)));
}

function obtenerTodosEventos() {
    return obtenerEventosBaseVisibles().concat(obtenerEventosPublicados().map(evento => ({
        id: evento.id,
        n: evento.nombre
    })));
}

function crearTarjetaEvento(evento) {
    const fechas = evento.fechas.map(fecha => `<li>&#128197; ${fecha}</li>`).join('');
    const etiquetaOrigen = esEventoSQLite(evento) ? '<span class="tag-sqlite">SQLite</span>' : '';
    const descripcion = evento.descripcion ? `<p class="descripcion-evento">${escaparHTML(evento.descripcion)}</p>` : '';

    return `
        <div class="artista evento-dinamico" id="${evento.id}">
            <button class="btn-edit" onclick="abrirEditor('${evento.id}')">&#9881; Cambiar fechas</button>
            <button class="btn-delete-evento" onclick="eliminarEventoPublicado('${evento.id}')">Eliminar</button>
            <img src="${evento.imagen}" alt="${escaparHTML(evento.nombre)}">
            <div class="info">
                <h3>${escaparHTML(evento.nombre)}</h3>
                ${etiquetaOrigen}
                ${descripcion}
                <div class="agenda">
                    <p class="disponible">&#9679; Agenda disponible</p>
                    <ul class="lista-agenda">
                        ${fechas}
                    </ul>
                </div>
                <button class="btn btn-principal" onclick="abrirInvitados('${evento.id}')">Reservar / Invitados</button>
                <button class="btn" onclick="saltarARaider('${evento.id}')" style="background:#2196F3; font-size:12px;">Ver Rider Tecnico</button>
            </div>
        </div>
    `;
}

function esEventoPublicado(id) {
    return obtenerEventosPublicados().some(evento => evento.id === id);
}

function eliminarEventoPublicado(id) {
    if (!confirm('¿Eliminar este evento publicado?')) return;

    const eventos = obtenerEventosPublicados().filter(evento => evento.id !== id);
    guardarEventosPublicados(eventos);
    limpiarDatosEvento(id);
    renderEventosPublicados();
    actualizarSelectRider();
    actualizarTablaRider();
}

function limpiarDatosEvento(id) {
    localStorage.removeItem('reserva_' + id);
    localStorage.removeItem('fecha_reserva_' + id);
    localStorage.removeItem('inv_' + id);
    fetch(urlRider(id), { method: 'DELETE' }).catch(() => {});
    eliminarEventoVistaUsuario(id);
    eliminarReservaAdministrador(id);
}

function eliminarEventoBooking(id) {
    if (esEventoPublicado(id)) {
        eliminarEventoPublicado(id);
        return;
    }

    if (!confirm('¿Eliminar este evento de la cartelera?')) return;

    const eliminados = obtenerEventosBaseEliminados();
    if (!eliminados.includes(id)) {
        eliminados.push(id);
        guardarEventosBaseEliminados(eliminados);
    }

    limpiarDatosEvento(id);
    const tarjeta = document.getElementById(id);
    if (tarjeta) tarjeta.remove();
    actualizarSelectRider();
    actualizarTablaRider();
}

function prepararBotonesEliminarEventosBase() {
    EVENTOS_BASE.forEach(evento => {
        const tarjeta = document.getElementById(evento.id);
        if (!tarjeta || tarjeta.querySelector('.btn-delete-evento')) return;

        const boton = document.createElement('button');
        boton.className = 'btn-delete-evento';
        boton.textContent = 'Eliminar';
        boton.onclick = () => eliminarEventoBooking(evento.id);
        tarjeta.insertBefore(boton, tarjeta.querySelector('img'));
    });
}

function aplicarEventosBaseEliminados() {
    obtenerEventosBaseEliminados().forEach(id => {
        const tarjeta = document.getElementById(id);
        if (tarjeta) tarjeta.remove();
    });
}

function renderEventosPublicados() {
    const contenedor = document.querySelector('#modulo-booking .container');
    if (!contenedor) return;

    contenedor.querySelectorAll('.evento-dinamico').forEach(evento => evento.remove());
    const eventos = obtenerEventosPublicados();
    contenedor.insertAdjacentHTML('beforeend', eventos.map(crearTarjetaEvento).join(''));
}

function actualizarVisibilidadFormularioEvento() {
    const formulario = document.querySelector('.form-publicar-evento');
    if (!formulario) return;

    formulario.style.display = riderFiltroActual ? 'none' : 'block';
}
function actualizarSelectRider() {
    const select = document.getElementById('selectArtistaRider');
    if (!select) return;

    const valorActual = select.value;
    const eventos = riderFiltroActual
        ? obtenerTodosEventos().filter(evento => evento.id === riderFiltroActual)
        : obtenerTodosEventos();

    select.innerHTML = eventos
        .map(evento => `<option value="${evento.id}">${evento.n}</option>`)
        .join('');

    if (riderFiltroActual) {
        select.value = riderFiltroActual;
        select.disabled = true;
    } else {
        select.disabled = false;
        if (valorActual) select.value = valorActual;
    }
}

function formatearHoraEvento(valor = '') {
    if (!valor) return '';
    const partes = valor.split(':');
    if (partes.length < 2) return valor;

    let horas = parseInt(partes[0], 10);
    const minutos = partes[1];
    const periodo = horas >= 12 ? 'PM' : 'AM';
    horas = horas % 12 || 12;
    return `${horas}:${minutos} ${periodo}`;
}

function convertirHoraAInput(valor = '') {
    if (!valor) return '';
    const texto = String(valor).trim();
    if (/^\d{2}:\d{2}$/.test(texto)) return texto;

    const match = texto.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if (!match) return '';

    let horas = parseInt(match[1], 10);
    const minutos = match[2];
    const periodo = match[3].toUpperCase();

    if (periodo === 'PM' && horas < 12) horas += 12;
    if (periodo === 'AM' && horas === 12) horas = 0;

    return `${String(horas).padStart(2, '0')}:${minutos}`;
}

function obtenerEventoPublicadoPorId(id) {
    return obtenerEventosPublicados().find(evento => evento.id === id) || null;
}

function sincronizarEventoBaseVistaUsuario(id, cambios) {
    const eventoBase = EVENTOS_BASE.find(evento => evento.id === id);
    if (!eventoBase) return;

    const agendasBase = JSON.parse(localStorage.getItem('eventos_base_agenda')) || [];
    const indice = agendasBase.findIndex(evento => evento.id === id);
    const registro = Object.assign({ id: id, nombre: eventoBase.n }, cambios);

    if (indice >= 0) agendasBase[indice] = Object.assign({}, agendasBase[indice], registro);
    else agendasBase.push(registro);

    localStorage.setItem('eventos_base_agenda', JSON.stringify(agendasBase));
}
function sincronizarEventoVistaUsuario(id, cambios) {
    const cartelera = JSON.parse(localStorage.getItem('cartelera_usuario')) || [];
    let actualizado = false;
    const nuevaCartelera = cartelera.map(evento => {
        if (evento.id !== id) return evento;
        actualizado = true;
        return Object.assign({}, evento, cambios);
    });

    if (actualizado) {
        localStorage.setItem('cartelera_usuario', JSON.stringify(nuevaCartelera));
    }
}
async function actualizarEventoSQLite(evento) {
    if (!esEventoSQLite(evento) || !evento.sqliteId) return;

    const agenda = (evento.fechas || []).map((fecha, index) => {
        const datosFecha = separarFechaLugar(fecha);
        return {
            fecha: datosFecha.fecha,
            lugar: datosFecha.lugar || evento.lugar,
            hora: evento.horas && evento.horas[index] ? evento.horas[index] : evento.hora
        };
    });

    const respuesta = await fetch(urlActualizarEventoSQLite(evento.sqliteId), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            nombre: evento.nombre,
            descripcion: evento.descripcion || '',
            lugar: evento.lugar || '',
            hora: evento.hora || '',
            imagen: evento.imagen || '',
            agenda: agenda
        })
    });

    const resultado = await respuesta.json();
    if (!respuesta.ok || !resultado.ok) {
        throw new Error(resultado.error || 'No se pudo actualizar el evento en SQLite.');
    }
}
function formatearFechaEvento(valor) {
    if (!valor) return '';

    const fecha = new Date(valor + 'T00:00:00');
    return fecha.toLocaleDateString('es-CO', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
    });
}

function limpiarFormularioEvento() {
    document.getElementById('nuevoEventoNombre').value = '';
    document.getElementById('nuevoEventoTipo').value = '';
    document.getElementById('nuevoEventoLugar').value = '';
    document.getElementById('nuevoEventoHora').value = '';
    document.getElementById('nuevoEventoFecha1').value = '';
    document.getElementById('nuevoEventoFecha2').value = '';
    document.getElementById('nuevoEventoFecha3').value = '';
    document.getElementById('nuevoEventoFoto').value = '';
}

function publicarEventoNuevo() {
    const nombre = document.getElementById('nuevoEventoNombre').value.trim();
    const tipo = document.getElementById('nuevoEventoTipo').value;
    const lugar = document.getElementById('nuevoEventoLugar').value;
    const hora = document.getElementById('nuevoEventoHora').value;
    const fechas = [
        document.getElementById('nuevoEventoFecha1').value,
        document.getElementById('nuevoEventoFecha2').value,
        document.getElementById('nuevoEventoFecha3').value
    ].filter(Boolean).map(fecha => `${formatearFechaEvento(fecha)} - ${lugar}`);
    const archivo = document.getElementById('nuevoEventoFoto').files[0];

    if (!nombre || !tipo || !lugar || !hora || fechas.length === 0 || !archivo) {
        alert('Completa nombre, tipo de evento, localidad, hora, al menos una fecha y una foto del evento.');
        return;
    }

    // Guardar fechas raw antes de que el FileReader sea asíncrono
    const fechasRaw = [
        document.getElementById('nuevoEventoFecha1').value,
        document.getElementById('nuevoEventoFecha2').value,
        document.getElementById('nuevoEventoFecha3').value
    ].filter(Boolean);

    const lector = new FileReader();
    lector.onload = async function (e) {
        const horaFormateada = formatearHoraEvento(hora);
        const imagenBase64   = e.target.result;

        // Agenda para la API: fechas en YYYY-MM-DD (valor crudo del input date)
        const agendaAPI = fechasRaw.map(f => ({ fecha: f, hora: hora, lugar: lugar }));

        // 1. Intentar persistir en SQLite vía Flask (enviamos la imagen completa solo aquí)
        let sqliteId    = null;
        let idFinal     = 'evento_' + Date.now();
        let imagenGuardar = IMAGEN_EVENTO_SQLITE; // placeholder si no hay servidor

        try {
            const respuesta = await fetch(API_EVENTOS_URL, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nombre:      nombre,
                    descripcion: '',
                    hora:        hora,
                    lugar:       lugar,
                    imagen:      imagenBase64,
                    agenda:      agendaAPI
                })
            });
            const resultado = await respuesta.json();
            if (respuesta.ok && resultado.ok) {
                sqliteId      = resultado.evento.id;
                idFinal       = 'sqlite_' + sqliteId;
                // La imagen ya está en SQLite; aquí guardamos solo la base64
                // para mostrarla en la tarjeta del Booking sin recargar la página
                imagenGuardar = imagenBase64;
            }
        } catch (err) {
            console.warn('Flask no disponible, evento queda solo en localStorage:', err);
        }

        // 2. Guardar en localStorage SIN la imagen base64 pesada cuando no hay servidor
        //    (si hay SQLite la imagen se recupera de la API en la próxima carga)
        const eventos     = obtenerEventosPublicados();
        const nuevoEvento = {
            id:       idFinal,
            sqliteId: sqliteId,
            origen:   sqliteId ? 'sqlite' : 'local',
            nombre:   nombre,
            tipo:     tipo,
            lugar:    lugar,
            hora:     horaFormateada,
            horas:    fechas.map(() => horaFormateada),
            fechas:   fechas,
            // Guardamos base64 solo si SQLite confirmó (para mostrar inmediatamente)
            // Si no hay servidor usamos placeholder para no saturar localStorage
            imagen:   imagenGuardar
        };
        eventos.push(nuevoEvento);

        try {
            guardarEventosPublicados(eventos);
        } catch (storageErr) {
            // localStorage lleno: guardar sin imagen
            nuevoEvento.imagen = IMAGEN_EVENTO_SQLITE;
            guardarEventosPublicados(eventos);
        }

        // 3. Sincronizar con cartelera_usuario (también sin imagen pesada si no hubo SQLite)
        try {
            const cartelera = JSON.parse(localStorage.getItem('cartelera_usuario')) || [];
            if (!cartelera.some(ev => ev.id === nuevoEvento.id)) {
                cartelera.push({
                    id:          nuevoEvento.id,
                    nombre:      nuevoEvento.nombre,
                    tipo:        nuevoEvento.tipo,
                    lugar:       nuevoEvento.lugar,
                    hora:        nuevoEvento.hora,
                    horas:       nuevoEvento.horas,
                    fechas:      nuevoEvento.fechas,
                    imagen:      nuevoEvento.imagen,
                    descripcion: ''
                });
                localStorage.setItem('cartelera_usuario', JSON.stringify(cartelera));
            }
        } catch (storageErr) {
            console.warn('No se pudo sincronizar cartelera_usuario:', storageErr);
        }

        renderEventosPublicados();
        actualizarSelectRider();
        actualizarTablaRider();
        limpiarFormularioEvento();
        mostrarModulo('booking');

        const msg = sqliteId
            ? `✅ Evento guardado en la base de datos (ID ${sqliteId}).\nQueda pendiente subir el rider técnico.`
            : '⚠️ Servidor no disponible. Evento publicado solo localmente.\nQueda pendiente subir el rider técnico.';
        alert(msg);
    };

    lector.readAsDataURL(archivo);
}

function volverAdministrador() {
    localStorage.setItem('admin_entrar_menu', 'true');
    window.location.href = '../JVS FRONTED ADMINISTRADOR/index.html';
}
function obtenerNombreArtista(id) {
    const tarjeta = document.getElementById(id);
    return tarjeta ? tarjeta.querySelector('h3').innerText : id;
}

function obtenerFechasDisponibles(id) {
    const tarjeta = document.getElementById(id);
    if (!tarjeta) return [];

    return Array.from(tarjeta.querySelectorAll('.lista-agenda li'))
        .map(item => item.innerText.replace(/^\D*(?=\d)/, '').trim())
        .filter(Boolean);
}

function cargarFechasReserva(id) {
    const select = document.getElementById('selectFechaReserva');
    const fechaGuardada = localStorage.getItem('fecha_reserva_' + id) || '';
    const fechas = obtenerFechasDisponibles(id);

    select.innerHTML = '<option value="">Seleccione una fecha disponible</option>';
    fechas.forEach(fecha => {
        const option = document.createElement('option');
        option.value = fecha;
        option.textContent = fecha;
        if (fecha === fechaGuardada) option.selected = true;
        select.appendChild(option);
    });
}

function guardarReservaAdministrador(id, fecha) {
    const invitados = JSON.parse(localStorage.getItem('inv_' + id)) || [];
    const reservas = JSON.parse(localStorage.getItem('reservas_eventos')) || [];
    const reserva = {
        id: id,
        artista: obtenerNombreArtista(id),
        fecha: fecha,
        invitados: invitados.map(inv => inv.nombre),
        totalInvitados: invitados.length,
        actualizada: new Date().toLocaleString('es-CO')
    };

    const filtradas = reservas.filter(item => item.id !== id);
    filtradas.push(reserva);
    localStorage.setItem('reservas_eventos', JSON.stringify(filtradas));
}

function eliminarReservaAdministrador(id) {
    const reservas = JSON.parse(localStorage.getItem('reservas_eventos')) || [];
    localStorage.setItem('reservas_eventos', JSON.stringify(reservas.filter(item => item.id !== id)));
}

function limpiarImagenesBase64LocalStorage() {
    // Las imágenes base64 en localStorage pueden saturarlo (límite ~5MB).
    // Si un evento ya está en SQLite (origen='sqlite'), su imagen viene de la API,
    // no necesita guardarse en localStorage. La limpiamos para liberar espacio.
    try {
        const eventos = obtenerEventosPublicados();
        let cambio = false;
        eventos.forEach(ev => {
            if (ev.imagen && ev.imagen.startsWith('data:') && ev.origen === 'sqlite') {
                ev.imagen = IMAGEN_EVENTO_SQLITE;
                cambio = true;
            }
        });
        if (cambio) guardarEventosPublicados(eventos);

        const cartelera = JSON.parse(localStorage.getItem('cartelera_usuario')) || [];
        let cambioCar = false;
        cartelera.forEach(ev => {
            if (ev.imagen && ev.imagen.startsWith('data:') && String(ev.id).startsWith('sqlite_')) {
                ev.imagen = IMAGEN_EVENTO_SQLITE;
                cambioCar = true;
            }
        });
        if (cambioCar) localStorage.setItem('cartelera_usuario', JSON.stringify(cartelera));
    } catch (err) {
        console.warn('Error limpiando base64 de localStorage:', err);
    }
}

window.onload = function () {
    limpiarImagenesBase64LocalStorage();
    cargarEventosDesdeAPI();
    prepararBotonesEliminarEventosBase();
    aplicarEventosBaseEliminados();
    renderEventosPublicados();
    actualizarSelectRider();

    obtenerTodosEventos().forEach(evento => {
        if (localStorage.getItem('reserva_' + evento.id) === 'true') {
            marcarComoReservado(evento.id);
        }
    });
};

// --- LÓGICA DE NAVEGACIÓN ---
function mostrarModulo(idMod) {
    document.querySelectorAll('.modulo').forEach(m => m.classList.remove('active'));
    document.querySelectorAll('.btn-nav').forEach(b => b.classList.remove('active'));

    document.getElementById('modulo-' + idMod).classList.add('active');
    const botonModulo = document.getElementById('btn-' + idMod);
    if (botonModulo) botonModulo.classList.add('active');

    if (idMod === 'raider') {
        actualizarVisibilidadFormularioEvento();
        actualizarSelectRider();
        actualizarTablaRider();
    }
}

function abrirRaiderGeneral() {
    riderFiltroActual = null;
    actualizarVisibilidadFormularioEvento();
    mostrarModulo('raider');
}

function saltarARaider(id) {
    riderFiltroActual = id;
    actualizarVisibilidadFormularioEvento();
    actualizarSelectRider();
    document.getElementById('selectArtistaRider').value = id;
    mostrarModulo('raider');
}

function escaparHTML(valor = '') {
    return valor
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function separarFechaLugar(valor = '') {
    const partes = valor.split(' - ');
    if (partes.length < 2) {
        return { fecha: valor.trim(), lugar: '' };
    }

    const lugar = partes.pop().trim();
    return {
        fecha: partes.join(' - ').trim(),
        lugar
    };
}

function crearOpcionesLugar(lugarActual = '') {
    const lugares = lugarActual && !LOCALIDADES_EVENTO.includes(lugarActual)
        ? [lugarActual].concat(LOCALIDADES_EVENTO)
        : LOCALIDADES_EVENTO;

    return '<option value="">Escoge el lugar</option>' + lugares.map(lugar => {
        const seleccionado = lugar === lugarActual ? 'selected' : '';
        return `<option value="${escaparHTML(lugar)}" ${seleccionado}>${escaparHTML(lugar)}</option>`;
    }).join('');
}

function crearCampoFecha(valor = '', hora = '') {
    const contenedor = document.getElementById('camposFechasAgenda');
    const fila = document.createElement('div');
    const datos = separarFechaLugar(valor);
    fila.className = 'fila-fecha-agenda';
    fila.innerHTML = `
        <label class="campo-agenda-fecha">
            <span>Fecha</span>
            <input type="text" class="inputFechaAgenda" value="${escaparHTML(datos.fecha)}" placeholder="Ej: 20 Marzo 2026">
        </label>
        <label class="campo-agenda-fecha">
            <span>Ciudad</span>
            <select class="selectLugarAgenda">${crearOpcionesLugar(datos.lugar)}</select>
        </label>
        <label class="campo-agenda-fecha">
            <span>Hora</span>
            <input type="time" class="inputHoraAgenda" value="${escaparHTML(convertirHoraAInput(hora))}">
        </label>
        <button type="button" class="btn-quitar-fecha" onclick="quitarCampoFecha(this)">Quitar</button>
    `;
    contenedor.appendChild(fila);
}

function agregarCampoFecha() {
    crearCampoFecha('');
}

function quitarCampoFecha(boton) {
    const filas = document.querySelectorAll('.fila-fecha-agenda');
    if (filas.length === 1) {
        alert('Debe quedar al menos una fecha.');
        return;
    }

    boton.closest('.fila-fecha-agenda').remove();
}
// --- LÓGICA DE AGENDA ---
function abrirEditor(id) {
    artistaIdActual = id;
    const tarjeta = document.getElementById(id);
    const nombreArt = tarjeta.querySelector('h3').innerText;
    const eventoPublicado = obtenerEventoPublicadoPorId(id);
    document.getElementById('editTitle').innerText = "Editar evento: " + nombreArt;

    const inputImagenUrl = document.getElementById('editEventoImagenUrl');
    const inputImagenArchivo = document.getElementById('editEventoImagenArchivo');
    const inputDescripcion = document.getElementById('editEventoDescripcion');
    const selectUbicacion = document.getElementById('editEventoUbicacion');

    if (inputImagenUrl) inputImagenUrl.value = eventoPublicado ? (eventoPublicado.imagen || '') : '';
    if (inputImagenArchivo) inputImagenArchivo.value = '';
    if (inputDescripcion) inputDescripcion.value = eventoPublicado ? (eventoPublicado.descripcion || '') : '';
    if (selectUbicacion) selectUbicacion.innerHTML = crearOpcionesLugar(eventoPublicado ? (eventoPublicado.lugar || '') : '');

    const contenedor = document.getElementById('camposFechasAgenda');
    contenedor.innerHTML = '';

    const fechasDesdeTarjeta = Array.from(tarjeta.querySelectorAll('.lista-agenda li'))
        .map(item => item.innerText.replace(/^[^A-Za-z0-9]+/, '').trim())
        .filter(Boolean);
    const fechas = eventoPublicado && Array.isArray(eventoPublicado.fechas) && eventoPublicado.fechas.length
        ? eventoPublicado.fechas
        : fechasDesdeTarjeta;
    const horas = eventoPublicado && Array.isArray(eventoPublicado.horas) ? eventoPublicado.horas : [];
    const horaBase = eventoPublicado ? eventoPublicado.hora || '' : '';

    if (fechas.length === 0) {
        crearCampoFecha('', horaBase);
    } else {
        fechas.forEach((fecha, index) => crearCampoFecha(fecha, horas[index] || horaBase));
    }

    document.getElementById('miModal').style.display = "block";
}

function cerrarModal() {
    document.getElementById('miModal').style.display = "none";
}

function guardarAgenda() {
    const tarjeta = document.getElementById(artistaIdActual);
    const lista = tarjeta.querySelector('.lista-agenda');
    const filas = Array.from(document.querySelectorAll('.fila-fecha-agenda'));
    const entradas = filas.map(fila => ({
        fecha: fila.querySelector('.inputFechaAgenda').value.trim(),
        lugar: fila.querySelector('.selectLugarAgenda').value.trim(),
        hora: fila.querySelector('.inputHoraAgenda').value.trim()
    }));

    const camposIncompletos = entradas.some(entrada => {
        const tieneAlgo = entrada.fecha || entrada.lugar || entrada.hora;
        return tieneAlgo && (!entrada.fecha || !entrada.lugar || !entrada.hora);
    });

    if (camposIncompletos) {
        alert('Cada registro debe tener fecha, ciudad y hora.');
        return;
    }

    const entradasValidas = entradas.filter(entrada => entrada.fecha && entrada.lugar && entrada.hora);

    if (entradasValidas.length === 0) {
        alert('Agrega al menos una fecha con ciudad y hora.');
        return;
    }

    const nuevasFechas = entradasValidas.map(entrada => `${entrada.fecha} - ${entrada.lugar}`);
    const nuevasHoras = entradasValidas.map(entrada => formatearHoraEvento(entrada.hora));
    const ubicacionEditor = document.getElementById('editEventoUbicacion') ? document.getElementById('editEventoUbicacion').value : '';
    const primeraUbicacion = ubicacionEditor || entradasValidas[0].lugar;
    const primeraHora = nuevasHoras[0];
    const descripcionEditada = document.getElementById('editEventoDescripcion') ? document.getElementById('editEventoDescripcion').value.trim() : '';
    const imagenUrlEditada = document.getElementById('editEventoImagenUrl') ? document.getElementById('editEventoImagenUrl').value.trim() : '';
    const archivoImagenEditada = document.getElementById('editEventoImagenArchivo') ? document.getElementById('editEventoImagenArchivo').files[0] : null;

    lista.innerHTML = nuevasFechas.map(fecha => `<li>&#128197; ${fecha}</li>`).join('');

    const cambiosAgenda = {
        fechas: nuevasFechas,
        horas: nuevasHoras,
        lugar: primeraUbicacion,
        hora: primeraHora,
        descripcion: descripcionEditada
    };
    if (imagenUrlEditada) cambiosAgenda.imagen = imagenUrlEditada;

    const guardarCambiosPublicados = (imagenArchivo = '') => {
        if (imagenArchivo) cambiosAgenda.imagen = imagenArchivo;

        if (esEventoPublicado(artistaIdActual)) {
            let eventoActualizado = null;
            const eventos = obtenerEventosPublicados().map(evento => {
                if (evento.id === artistaIdActual) {
                    evento.fechas = nuevasFechas;
                    evento.horas = nuevasHoras;
                    evento.lugar = primeraUbicacion;
                    evento.hora = primeraHora;
                    evento.descripcion = descripcionEditada;
                    if (imagenUrlEditada) evento.imagen = imagenUrlEditada;
                    if (imagenArchivo) evento.imagen = imagenArchivo;
                    eventoActualizado = evento;
                }
                return evento;
            });
            guardarEventosPublicados(eventos);
            sincronizarEventoVistaUsuario(artistaIdActual, cambiosAgenda);
            if (eventoActualizado && esEventoSQLite(eventoActualizado)) {
                actualizarEventoSQLite(eventoActualizado)
                    .catch(error => alert(error.message || 'No se pudo actualizar SQLite.'));
            }
            renderEventosPublicados();
            actualizarSelectRider();
            actualizarTablaRider();
        } else {
            sincronizarEventoBaseVistaUsuario(artistaIdActual, cambiosAgenda);
        }

        cerrarModal();
    };

    if (archivoImagenEditada && esEventoPublicado(artistaIdActual)) {
        const lector = new FileReader();
        lector.onload = function(e) {
            guardarCambiosPublicados(e.target.result);
        };
        lector.readAsDataURL(archivoImagenEditada);
        return;
    }

    guardarCambiosPublicados();
}
// --- Lógica de Invitados ---
function abrirInvitados(id) {
    artistaIdActual = id;
    const nombreArt = document.getElementById(id).querySelector('h3').innerText;
    document.getElementById('invitadosTitle').innerText = "Invitados: " + nombreArt;

    const btnQuitar = document.getElementById('btnQuitarReserva');
    btnQuitar.style.display = localStorage.getItem('reserva_' + id) === 'true' ? "block" : "none";

    cargarFechasReserva(id);
    renderizarInvitados();
    document.getElementById('modalInvitados').style.display = "block";
}

function cerrarModalInvitados() {
    document.getElementById('modalInvitados').style.display = "none";
}

function agregarInvitado() {
    const inputNombre = document.getElementById('inputNombreInv');
    const inputFoto = document.getElementById('inputFotoInv');
    if (inputNombre.value.trim() === "") return alert("Escribe un nombre.");

    const lector = new FileReader();
    lector.onload = function (e) {
        const nuevoInvitado = {
            id: Date.now(),
            nombre: inputNombre.value,
            foto: e.target.result || 'https://cdn-icons-png.flaticon.com/512/149/149071.png'
        };
        let almacen = JSON.parse(localStorage.getItem('inv_' + artistaIdActual)) || [];
        almacen.push(nuevoInvitado);
        localStorage.setItem('inv_' + artistaIdActual, JSON.stringify(almacen));
        inputNombre.value = "";
        inputFoto.value = "";
        renderizarInvitados();
    };

    if (inputFoto.files[0]) lector.readAsDataURL(inputFoto.files[0]);
    else lector.onload({ target: { result: 'https://cdn-icons-png.flaticon.com/512/149/149071.png' } });
}

function renderizarInvitados() {
    const listaUI = document.getElementById('listaNombres');
    listaUI.innerHTML = "";
    const datos = JSON.parse(localStorage.getItem('inv_' + artistaIdActual)) || [];
    datos.forEach(inv => {
        const li = document.createElement('li');
        li.className = "invitado-item";
        li.innerHTML = `
            <img src="${inv.foto}">
            <div style="flex-grow:1"><b>${inv.nombre}</b></div>
            <button class="btn-del" onclick="borrarInvitado(${inv.id})">Borrar</button>
        `;
        listaUI.appendChild(li);
    });
}

function borrarInvitado(idInv) {
    let datos = JSON.parse(localStorage.getItem('inv_' + artistaIdActual)) || [];
    datos = datos.filter(item => item.id !== idInv);
    localStorage.setItem('inv_' + artistaIdActual, JSON.stringify(datos));
    renderizarInvitados();
}

// --- LÓGICA DE RAIDER TÉCNICO ---
function leerArchivoComoBase64(archivo) {
    return new Promise((resolve, reject) => {
        const lector = new FileReader();
        lector.onload = (e) => resolve(e.target.result);
        lector.onerror = () => reject(new Error('No se pudo leer el archivo.'));
        lector.readAsDataURL(archivo);
    });
}

async function vincularRider() {
    const artId = document.getElementById('selectArtistaRider').value;
    const fileInput = document.getElementById('inputArchivoRider');

    if (fileInput.files.length === 0) return alert("Selecciona un archivo primero.");

    const archivo = fileInput.files[0];

    try {
        const contenidoBase64 = await leerArchivoComoBase64(archivo);

        const respuesta = await fetch(urlRider(artId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre_archivo: archivo.name,
                tipo_archivo: archivo.type,
                contenido_base64: contenidoBase64
            })
        });

        const resultado = await respuesta.json();
        if (!respuesta.ok || !resultado.ok) throw new Error(resultado.error || 'No se pudo guardar el rider.');

        fileInput.value = '';
        alert("Rider guardado y listo para abrir.");
        await actualizarTablaRider();
    } catch (error) {
        alert(error.message || "No se pudo guardar el rider. Verifica tu conexion con el servidor.");
    }
}

async function abrirRider(id) {
    try {
        const respuesta = await fetch(urlRider(id));
        const resultado = await respuesta.json();
        if (!respuesta.ok || !resultado.ok) throw new Error(resultado.error || 'No hay archivo vinculado.');

        const win = window.open();
        win.document.write(
            '<iframe src="' + resultado.rider.contenido_base64 +
            '" frameborder="0" style="border:0; top:0px; left:0px; bottom:0px; right:0px; width:100%; height:100%;" allowfullscreen></iframe>'
        );
    } catch (error) {
        alert(error.message || "No se pudo abrir el rider.");
    }
}

async function actualizarTablaRider() {
    const cuerpo = document.getElementById('cuerpoTablaRider');
    if (!cuerpo) return;

    const artistas = riderFiltroActual
        ? obtenerTodosEventos().filter(evento => evento.id === riderFiltroActual)
        : obtenerTodosEventos();

    let riders = [];
    try {
        const respuesta = await fetch(API_RIDERS_URL);
        const resultado = await respuesta.json();
        if (respuesta.ok && resultado.ok) riders = resultado.riders;
    } catch (error) {
        console.warn('No se pudieron cargar los riders desde el servidor:', error);
    }

    const ridersPorArtista = {};
    riders.forEach(r => { ridersPorArtista[r.artista_id] = r; });

    cuerpo.innerHTML = artistas.map(a => {
        const archivo = ridersPorArtista[a.id] || null;
        return `
            <tr>
                <td><b>${a.n}</b></td>
                <td style="color: ${archivo ? 'green' : 'red'}">${archivo ? '✅ Recibido' : '❌ Pendiente'}</td>
                <td>${archivo ? archivo.nombre_archivo : '---'}</td>
                <td>
                    ${archivo
                        ? `<button onclick="abrirRider('${a.id}')" style="background:#2196F3; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;">👁️ Abrir</button>`
                        : '---'}
                </td>
                <td>
                    ${archivo
                        ? `<button onclick="eliminarRider('${a.id}')" style="color:red; cursor:pointer; background:none; border:none;">Eliminar</button>`
                        : '---'}
                </td>
            </tr>
        `;
    }).join('');
}

async function eliminarRider(id) {
    if (!confirm("¿Eliminar archivo técnico?")) return;

    try {
        const respuesta = await fetch(urlRider(id), { method: 'DELETE' });
        const resultado = await respuesta.json();
        if (!respuesta.ok || !resultado.ok) throw new Error(resultado.error || 'No se pudo eliminar el rider.');
        await actualizarTablaRider();
    } catch (error) {
        alert(error.message || "No se pudo eliminar el rider.");
    }
}

// --- LÓGICA DE RESERVA Y QUITAR RESERVA ---
function confirmarYReservar() {
    const fechaSeleccionada = document.getElementById('selectFechaReserva').value;

    if (!fechaSeleccionada) {
        alert("Selecciona la fecha que desea reservar el invitado.");
        return;
    }

    if (confirm("¿Deseas finalizar y reservar esta fecha?")) {
        localStorage.setItem('reserva_' + artistaIdActual, 'true');
        localStorage.setItem('fecha_reserva_' + artistaIdActual, fechaSeleccionada);
        guardarReservaAdministrador(artistaIdActual, fechaSeleccionada);
        marcarComoReservado(artistaIdActual);
        cerrarModalInvitados();
    }
}

function quitarReserva() {
    if (confirm("¿Estás seguro de quitar la reserva de este artista? Se perderá el bloqueo visual.")) {
        localStorage.removeItem('reserva_' + artistaIdActual);
        localStorage.removeItem('fecha_reserva_' + artistaIdActual);
        eliminarReservaAdministrador(artistaIdActual);
        location.reload();
    }
}

function marcarComoReservado(id) {
    const tarjeta = document.getElementById(id);
    if (tarjeta) {
        tarjeta.classList.add('reservado-visual');
        const badge = tarjeta.querySelector('.disponible');
        if (badge) {
            const fecha = localStorage.getItem('fecha_reserva_' + id);
            badge.innerText = fecha ? "● RESERVADO - " + fecha : "● RESERVADO";
        }
        const btnPrincipal = tarjeta.querySelector('.btn-principal');
        if (btnPrincipal) {
            btnPrincipal.innerText = "Reserva Exitosa ✓";
            btnPrincipal.style.background = "#4CAF50";
        }
    }
}

window.onclick = function (event) {
    if (event.target.className === "modal") {
        cerrarModal();
        cerrarModalInvitados();
    }
};