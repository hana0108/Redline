// Función para abrir el modal y rellenar los datos dinámicamente
function abrirModal(titulo, precio, ano, carroceria, transmision, millaje, condicion, combustible) {
    // Buscamos los elementos por su ID y les asignamos el texto recibido
    document.getElementById('m-titulo').innerText = titulo;
    document.getElementById('m-precio').innerText = precio;
    document.getElementById('m-ano').innerText = ano;
    document.getElementById('m-carroceria').innerText = carroceria;
    document.getElementById('m-transmision').innerText = transmision;
    document.getElementById('m-millaje').innerText = millaje;
    document.getElementById('m-condicion').innerText = condicion;
    document.getElementById('m-combustible').innerText = combustible;

    // Mostramos el modal cambiando el estilo de display
    const modal = document.getElementById('modalVehiculo');
    modal.style.display = "block";
    
    // Evitamos que la página principal se mueva mientras el modal está abierto
    document.body.style.overflow = "hidden";
}

// Función para cerrar el modal
function cerrarModal() {
    const modal = document.getElementById('modalVehiculo');
    modal.style.display = "none";
    
    // Devolvemos el scroll a la página
    document.body.style.overflow = "auto";
}

// Cerrar automáticamente si el usuario hace clic fuera del cuadro blanco
window.onclick = function(event) {
    const modal = document.getElementById('modalVehiculo');
    if (event.target == modal) {
        cerrarModal();
    }
}

// Funcion de la busqueda y filtrado 
document.addEventListener('DOMContentLoaded', () => {
    const btnBuscar = document.querySelector('.btn-sidebar-search');
    
    btnBuscar.addEventListener('click', () => {
        const checkboxesMarcados = document.querySelectorAll('.brand-list input[type="checkbox"]:checked');
        const marcasSeleccionadas = Array.from(checkboxesMarcados).map(checkbox => {
            const marca = checkbox.value || checkbox.parentElement.textContent.trim().split(' ')[0];
            return marca.toLowerCase();
        });

        const tarjetasVehiculos = document.querySelectorAll('.car-card');

        tarjetasVehiculos.forEach(tarjeta => {
            const tituloVehiculo = tarjeta.querySelector('h4').textContent.toLowerCase();

            const debeMostrarse = marcasSeleccionadas.length === 0 || marcasSeleccionadas.some(marca => tituloVehiculo.includes(marca));

            if (debeMostrarse) {
                tarjeta.style.display = ''; 
            } else {
                tarjeta.style.display = 'none';
            }
        });
    });
});