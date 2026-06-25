let artistaIdActual = "";

window.onload = function () {
    const ids = ['art1', 'art2', 'art3', 'art4', 'art5', 'art6'];
    ids.forEach(id => {
        if (localStorage.getItem('reserva_' + id) === 'true') {
            marcarComoReservado(id);
        }
    });
};

// --- LÓGICA DE NAVEGACIÓN ---
function mostrarModulo(idMod) {
    document.querySelectorAll('.modulo').forEach(m => m.classList.remove('active'));
    document.querySelectorAll('.btn-nav').forEach(b => b.classList.remove('active'));

    document.getElementById('modulo-' + idMod).classList.add('active');
    document.getElementById('btn-' + idMod).classList.add('active');

    if (idMod === 'raider') actualizarTablaRider();
}

function saltarARaider(id) {
    document.getElementById('selectArtistaRider').value = id;
    mostrarModulo('raider');
}

// --- LÓGICA DE AGENDA ---
function abrirEditor(id) {
    artistaIdActual = id;
    const nombreArt = document.getElementById(id).querySelector('h3').innerText;
    document.getElementById('editTitle').innerText = "Cambiar fechas de: " + nombreArt;

    const items = document.getElementById(id).querySelectorAll('.lista-agenda li');
    document.getElementById('inputFecha1').value = items[0].innerText.replace('📅 ', '');
    document.getElementById('inputFecha2').value = items[1].innerText.replace('📅 ', '');
    document.getElementById('inputFecha3').value = items[2].innerText.replace('📅 ', '');
    document.getElementById('miModal').style.display = "block";
}

function cerrarModal() {
    document.getElementById('miModal').style.display = "none";
}

function guardarAgenda() {
    const lista = document.getElementById(artistaIdActual).querySelectorAll('.lista-agenda li');
    lista[0].innerHTML = `📅 ${document.getElementById('inputFecha1').value}`;
    lista[1].innerHTML = `📅 ${document.getElementById('inputFecha2').value}`;
    lista[2].innerHTML = `📅 ${document.getElementById('inputFecha3').value}`;
    cerrarModal();
}

// --- LÓGICA DE INVITADOS ---
function abrirInvitados(id) {
    artistaIdActual = id;
    const nombreArt = document.getElementById(id).querySelector('h3').innerText;
    document.getElementById('invitadosTitle').innerText = "Invitados: " + nombreArt;

    const btnQuitar = document.getElementById('btnQuitarReserva');
    btnQuitar.style.display = localStorage.getItem('reserva_' + id) === 'true' ? "block" : "none";

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
function vincularRider() {
    const artId = document.getElementById('selectArtistaRider').value;
    const fileInput = document.getElementById('inputArchivoRider');

    if (fileInput.files.length === 0) return alert("Selecciona un archivo primero.");

    const archivo = fileInput.files[0];
    const lector = new FileReader();

    lector.onload = function (e) {
        const datosArchivo = {
            nombre: archivo.name,
            tipo: archivo.type,
            contenido: e.target.result
        };
        localStorage.setItem('rider_obj_' + artId, JSON.stringify(datosArchivo));
        alert("Rider guardado y listo para abrir.");
        actualizarTablaRider();
    };

    lector.readAsDataURL(archivo);
}

function abrirRider(id) {
    const datosRaw = localStorage.getItem('rider_obj_' + id);
    if (!datosRaw) return alert("No hay archivo vinculado.");

    const datos = JSON.parse(datosRaw);
    const win = window.open();
    win.document.write(
        '<iframe src="' + datos.contenido +
        '" frameborder="0" style="border:0; top:0px; left:0px; bottom:0px; right:0px; width:100%; height:100%;" allowfullscreen></iframe>'
    );
}

function actualizarTablaRider() {
    const cuerpo = document.getElementById('cuerpoTablaRider');
    cuerpo.innerHTML = "";
    const artistas = [
        { id: 'art1', n: 'Feid' },
        { id: 'art2', n: 'Bad Bunny' },
        { id: 'art3', n: 'Romeo Santos' },
        { id: 'art4', n: 'Evento Techno' },
        { id: 'art5', n: 'Karol G' },
        { id: 'art6', n: 'Evento Rave' }
    ];

    artistas.forEach(a => {
        const datosRaw = localStorage.getItem('rider_obj_' + a.id);
        const archivo = datosRaw ? JSON.parse(datosRaw) : null;

        cuerpo.innerHTML += `
            <tr>
                <td><b>${a.n}</b></td>
                <td style="color: ${archivo ? 'green' : 'red'}">${archivo ? '✅ Recibido' : '❌ Pendiente'}</td>
                <td>${archivo ? archivo.nombre : '---'}</td>
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
    });
}

function eliminarRider(id) {
    if (confirm("¿Eliminar archivo técnico?")) {
        localStorage.removeItem('rider_obj_' + id);
        actualizarTablaRider();
    }
}

// --- LÓGICA DE RESERVA Y QUITAR RESERVA ---
function confirmarYReservar() {
    if (confirm("¿Deseas finalizar y reservar?")) {
        localStorage.setItem('reserva_' + artistaIdActual, 'true');
        marcarComoReservado(artistaIdActual);
        cerrarModalInvitados();
    }
}

function quitarReserva() {
    if (confirm("¿Estás seguro de quitar la reserva de este artista? Se perderá el bloqueo visual.")) {
        localStorage.removeItem('reserva_' + artistaIdActual);
        location.reload();
    }
}

function marcarComoReservado(id) {
    const tarjeta = document.getElementById(id);
    if (tarjeta) {
        tarjeta.classList.add('reservado-visual');
        const badge = tarjeta.querySelector('.disponible');
        if (badge) badge.innerText = "● RESERVADO";
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
