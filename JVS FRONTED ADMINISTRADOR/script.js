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

function mostrarMenuAdministrador() {
    document.getElementById("login").style.display = "none";
    document.getElementById("bienvenida").innerText = "Hola Admin, bienvenido";
}

window.addEventListener("DOMContentLoaded", function() {
    if (localStorage.getItem("admin_entrar_menu") === "true") {
        localStorage.removeItem("admin_entrar_menu");
        mostrarMenuAdministrador();
    }
});

// ===== LOGIN =====
function login() {
    const usuario   = document.getElementById("user").value;
    const contraseña = document.getElementById("pass").value;

    if (usuario === "admin" && contraseña === "1234") {
        mostrarMenuAdministrador();
    } else {
        alert("Datos incorrectos");
    }
}

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
    window.location.href = "../JVS FRONTED USUARIO/index.html";
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

function verProveedores() {
    window.location.href = "../JVS FRONTED PROVEEDORES/proveedores.html";
}