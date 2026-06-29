const productos = [
    {
        nombre: "Aguardiente Amarillo",
        stock: 10,
        precio: 25000,
        img: "imagen/aguardiente.jpg"
    },
    {
        nombre: "Cerveza Águila",
        stock: 20,
        precio: 4000,
        img: "imagen/aguila.webp"
    },
    {
        nombre: "Cerveza Corona",
        stock: 15,
        precio: 6000,
        img: "imagen/corona.webp"
    },
    {
        nombre: "Whisky",
        stock: 8,
        precio: 80000,
        img: "imagen/whisky.webp"
    }
];

let productoEditando = null;

async function mostrarMenuAdministrador() {
    try {
        const respuesta = await fetch("/api/sesion", { credentials: "include" });
        const datos = await respuesta.json();

        if (!datos.ok || !datos.autenticado) {
            window.location.href = "/web/login/";
            return;
        }

        const nombreCompleto = `${datos.nombre || ""} ${datos.apellido || ""}`.trim() || "Administrador";
        document.getElementById("bienvenida").innerText = `Hola ${datos.nombre || "Admin"}, bienvenido`;
        document.getElementById("nombreUsuario").innerText = nombreCompleto;
        document.getElementById("cedulaUsuario").innerText = `Cédula: ${datos.cedula || "No registrada"}`;
    } catch (error) {
        document.getElementById("bienvenida").innerText = "Hola Admin, bienvenido";
    }
}

window.addEventListener("DOMContentLoaded", function() {
    mostrarMenuAdministrador();
});

// ===== FOTO DE PERFIL =====
function showOptions() {
    const opt = document.getElementById("photoOptions");
    opt.style.display = opt.style.display === "block" ? "none" : "block";
}

function changePhoto(src) {
    document.getElementById("mainPhoto").src = src;
}

// ===== NAVEGACION =====
function abrirVistaUsuario() {
    window.location.href = "/web/app/";
}

// ===== MODAL COORDINADOR =====
function abrirCoord() {
    document.getElementById("ventanaCoord").style.display = "flex";
}

function cerrarCoord() {
    document.getElementById("ventanaCoord").style.display = "none";
}

// ===== MODAL VENDEDOR =====
function abrirVend() {
    document.getElementById("ventanaVend").style.display = "flex";
}

function cerrarVend() {
    document.getElementById("ventanaVend").style.display = "none";
}

// ===== MODAL SALARIO =====
function verSalario() {
    document.getElementById("ventanaSalario").style.display = "flex";
}

function cerrarSalario() {
    document.getElementById("ventanaSalario").style.display = "none";
}

// ===== INVENTARIO =====
function verInventarioVend() {
    document.getElementById("inventarioVend").style.display = "flex";
    renderInventario();
}

function cerrarInventario() {
    document.getElementById("inventarioVend").style.display = "none";
}

function renderInventario() {

    const contenedor = document.getElementById("listaInventario");

    contenedor.innerHTML = "";

    productos.forEach((p, i) => {

        contenedor.innerHTML += `

        <div class="producto-item">

            <img src="${p.img}" class="inventario-img">

            <div>

                <b>${p.nombre}</b><br><br>

                Precio: $${p.precio.toLocaleString("es-CO")}<br>

                Stock disponible: ${p.stock} unidades

                <div style="margin-top:10px;">

                    <button onclick="editarProducto(${i})">
                        Editar
                    </button>

                    <button onclick="eliminarProducto(${i})"
                    style="background:#7a0018;border:none;">
                        Eliminar
                    </button>

                </div>

            </div>

        </div>

        `;

      });

}

function eliminarProducto(i) {

    if (confirm("¿Seguro que quieres eliminar este producto?")) {

        productos.splice(i, 1);

        renderInventario();

    }

}

function editarProducto(i){

    productoEditando = i;

    document.getElementById("tituloModalProducto").innerText = "Editar producto";

    document.getElementById("nombreProducto").value = productos[i].nombre;

    document.getElementById("precioProducto").value = productos[i].precio;

    document.getElementById("stockProducto").value = productos[i].stock;

    document.getElementById("imagenProducto").value = "";

    document.getElementById("modalProducto").style.display = "flex";

}

function agregarProducto(){

    productoEditando = null;

    document.getElementById("tituloModalProducto").innerText = "Agregar producto";

    document.getElementById("nombreProducto").value = "";

    document.getElementById("precioProducto").value = "";

    document.getElementById("stockProducto").value = "";

    document.getElementById("imagenProducto").value = "";

    document.getElementById("modalProducto").style.display = "flex";

}

function guardarCambios() {
    alert("Cambios guardados correctamente");
}

function verVentasMes() {
    alert("Aun no hay ventas registradas este mes.");
}


// ===== RESERVAS DE EVENTOS =====
function abrirReservas() {
    document.getElementById("ventanaReservas").style.display = "flex";
    renderReservasAdministrador();
}

function cerrarReservas() {
    document.getElementById("ventanaReservas").style.display = "none";
}

function renderReservasAdministrador() {
    const contenedor = document.getElementById("listaReservasEventos");
    if (!contenedor) return;

    const reservas = JSON.parse(localStorage.getItem("reservas_eventos")) || [];

    if (reservas.length === 0) {
        contenedor.innerHTML = "<p style='text-align:center;'>Todavia no hay reservas registradas.</p>";
        return;
    }

    contenedor.innerHTML = reservas.map(reserva => {
        const invitados = reserva.invitados && reserva.invitados.length
            ? reserva.invitados.join(", ")
            : "Sin invitados registrados";

        return `
            <div class="producto-item">
                <div>
                    <b>${reserva.artista}</b><br><br>
                    Fecha reservada: ${reserva.fecha}<br>
                    Invitados (${reserva.totalInvitados || 0}): ${invitados}<br>
                    Actualizada: ${reserva.actualizada || "---"}
                </div>
            </div>
        `;
    }).join("");
}

window.addEventListener("storage", function(event) {
    if (event.key === "reservas_eventos") {
        renderReservasAdministrador();
    }
});

// ===== GESTION DE ROLES =====
let rolesCatalogo = [];
let usuariosRolesCache = [];

function abrirRoles() {
    document.getElementById("ventanaRoles").style.display = "flex";
    document.getElementById("rolesBuscador").value = "";
    cargarDatosRoles();
}

function cerrarRoles() {
    document.getElementById("ventanaRoles").style.display = "none";
}

function mostrarMensajeRoles(texto, esError = false) {
    const el = document.getElementById("rolesMensajeEstado");
    el.innerText = texto;
    el.style.color = esError ? "#ff4d4d" : "#ccc";
}

async function cargarDatosRoles() {
    mostrarMensajeRoles("Cargando usuarios...");
    try {
        const [respRoles, respUsuarios] = await Promise.all([
            fetch("/api/roles", { credentials: "include" }),
            fetch("/api/usuarios/roles", { credentials: "include" })
        ]);

        const datosRoles = await respRoles.json();
        const datosUsuarios = await respUsuarios.json();

        if (!respRoles.ok || !datosRoles.ok) {
            throw new Error(datosRoles.error || "No se pudo cargar el catalogo de roles");
        }
        if (!respUsuarios.ok || !datosUsuarios.ok) {
            throw new Error(datosUsuarios.error || "No se pudo cargar la lista de usuarios");
        }

        rolesCatalogo = datosRoles.roles;
        usuariosRolesCache = datosUsuarios.usuarios;
        mostrarMensajeRoles(`${usuariosRolesCache.length} usuario(s) encontrados.`);
        renderUsuariosRoles(usuariosRolesCache);
    } catch (error) {
        mostrarMensajeRoles("Error: " + error.message, true);
        document.getElementById("listaUsuariosRoles").innerHTML = "";
    }
}

function filtrarUsuariosRoles() {
    const termino = document.getElementById("rolesBuscador").value.trim().toLowerCase();
    if (!termino) {
        renderUsuariosRoles(usuariosRolesCache);
        return;
    }
    const filtrados = usuariosRolesCache.filter(u =>
        `${u.nombre} ${u.apellido}`.toLowerCase().includes(termino) ||
        (u.correo || "").toLowerCase().includes(termino)
    );
    renderUsuariosRoles(filtrados);
}

function renderUsuariosRoles(usuarios) {
    const contenedor = document.getElementById("listaUsuariosRoles");

    if (!usuarios.length) {
        contenedor.innerHTML = "<p style='text-align:center;'>No se encontraron usuarios.</p>";
        return;
    }

    contenedor.innerHTML = usuarios.map(usuario => {
        const idsActuales = usuario.roles.map(r => r.rol_id);

        const checkboxes = rolesCatalogo.map(rol => {
            const marcado = idsActuales.includes(rol.rol_id) ? "checked" : "";
            return `
                <label class="rol-checkbox-label">
                    <input type="checkbox" value="${rol.rol_id}" ${marcado}>
                    ${rol.nombre}
                </label>
            `;
        }).join("");

        return `
            <div class="usuario-rol-item" data-usuario-id="${usuario.usuario_id}">
                <div class="usuario-rol-info">
                    <div>
                        <b>${usuario.nombre} ${usuario.apellido}</b>
                        <span class="correo">${usuario.correo || "Sin correo registrado"}</span>
                    </div>
                    <span class="rol-actual-chip">${usuario.rol_nombre}</span>
                </div>
                <div class="roles-checkboxes">${checkboxes}</div>
                <div class="usuario-rol-acciones">
                    <span class="rol-guardado-ok" id="rolOk-${usuario.usuario_id}"></span>
                    <button onclick="guardarRolesUsuario(${usuario.usuario_id})">Guardar roles</button>
                </div>
            </div>
        `;
    }).join("");
}

async function guardarRolesUsuario(usuarioId) {
    const tarjeta = document.querySelector(`.usuario-rol-item[data-usuario-id="${usuarioId}"]`);
    if (!tarjeta) return;

    const seleccionados = Array.from(tarjeta.querySelectorAll(".roles-checkboxes input:checked"))
        .map(input => parseInt(input.value, 10));

    if (seleccionados.length === 0) {
        alert("Selecciona al menos un rol para este usuario.");
        return;
    }

    try {
        const respuesta = await fetch(`/api/usuarios/${usuarioId}/roles`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ roles: seleccionados })
        });
        const datos = await respuesta.json();

        if (!respuesta.ok || !datos.ok) {
            throw new Error(datos.error || "No se pudo actualizar el rol");
        }

        const indicador = document.getElementById(`rolOk-${usuarioId}`);
        indicador.innerText = "✔ Guardado";
        setTimeout(() => { indicador.innerText = ""; }, 2500);

        // Refrescar el chip del rol mas relevante y la cache local
        const usuario = usuariosRolesCache.find(u => u.usuario_id === usuarioId);
        if (usuario) {
            const rolPrincipal = rolesCatalogo.find(r => r.rol_id === datos.rol_id);
            usuario.rol_id = datos.rol_id;
            usuario.rol_nombre = rolPrincipal ? rolPrincipal.nombre : "Sin rol";
            usuario.roles = datos.roles.map(id => {
                const rol = rolesCatalogo.find(r => r.rol_id === id);
                return { rol_id: id, nombre: rol ? rol.nombre : "" };
            });
            tarjeta.querySelector(".rol-actual-chip").innerText = usuario.rol_nombre;
        }
    } catch (error) {
        alert("Error al guardar roles: " + error.message);
    }
}

// ===== OTRAS FUNCIONES =====
function verInventario() {
    window.location.href = "raider.html";
}
function cerrarModalProducto(){

    document.getElementById("modalProducto").style.display = "none";

}

function guardarProducto(){

    const nombre = document.getElementById("nombreProducto").value;

    const precio = parseInt(document.getElementById("precioProducto").value);

    const stock = parseInt(document.getElementById("stockProducto").value);

    const archivo = document.getElementById("imagenProducto").files[0];

    if (!nombre || Number.isNaN(precio) || Number.isNaN(stock)) {
        alert("Completa nombre, precio y stock antes de guardar.");
        return;
    }

    let imagen = "imagen/default.png";

    if(archivo){

        imagen = URL.createObjectURL(archivo);

    }

    if(productoEditando === null){

        productos.push({

            nombre,

            precio,

            stock,

            img: imagen

        });

    }else{

        productos[productoEditando].nombre = nombre;

        productos[productoEditando].precio = precio;

        productos[productoEditando].stock = stock;

        if(archivo){

            productos[productoEditando].img = imagen;

        }

    }

    cerrarModalProducto();

    renderInventario();

}

async function cerrarSesionAdmin() {
    try {
        await fetch("/api/logout", { method: "POST", credentials: "include" });
    } finally {
        window.location.href = "/web/login/";
    }
}

function verProveedores() {
    window.location.href = "/web/proveedores/";
}