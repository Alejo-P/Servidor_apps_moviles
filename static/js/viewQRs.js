async function getQRs() {
    const response = await fetch('/api/v1/qrs', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    data = await response.json();

    const qrArray = data.files;

    qrArray.forEach(async qr => {
        let qrDivPrincipal = document.getElementById("QRs");

        // Crear un div con la información del QR    
        let qrDiv = document.createElement("div");
        qrDiv.setAttribute("class", "flex flex-col items-center justify-center p-4 border border-gray-300 rounded-lg bg-gray-100");
        qrDivPrincipal.appendChild(qrDiv);

        let qrImage = document.createElement("img");
        qrImage.setAttribute("src", "/api/v1/qr/" + qr);
        qrImage.setAttribute("alt", "QR");
        qrImage.setAttribute("class", "w-48 h-48 rounded-lg border border-gray-300");
        qrDiv.appendChild(qrImage);

        let qrName = document.createElement("p");
        qrName.textContent = qr;
        qrName.setAttribute("class", "text-center text-blue-500 font-bold w-48 overflow-hidden whitespace-nowrap overflow-ellipsis");
        qrDiv.appendChild(qrName);

        // Añadir el div al div principal
        qrDivPrincipal.appendChild(qrDiv);
    });
}

async function getQR(name) {
    const response = await fetch(`/api/v1/qr/${name}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return response;
}

async function deleteQR(name) {
    const response = await fetch(`/api/v1/qr/${name}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    const jsonResponse = await response.json();
    document.getElementById("message").classList.remove("text-green-700", "text-red-500");

    if (response.ok) {
        document.getElementById("message").textContent = jsonResponse.message || jsonResponse.error;
        document.getElementById("message").classList.add("text-green-700");
    } else {
        document.getElementById("message").textContent = jsonResponse.message || jsonResponse.error;
        document.getElementById("message").classList.add("text-red-500");
    }

    setTimeout(() => {
        document.getElementById("message").textContent = "";
        getQRs();
    }, 3000);
}

async function downloadQR(name) {
    const response = await fetch(`/api/v1/download/qr/${name}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return response;
}

async function createQR() {
    let data = document.getElementById("QRtext").value;
    const response = await fetch('/api/v1/qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: data })
    });

    const jsonResponse = await response.json();

    document.getElementById("messageModal").classList.remove("text-green-700", "text-red-500");

    if (response.ok) {
        document.getElementById("messageModal").textContent = jsonResponse.message;
        document.getElementById("messageModal").classList.add("text-green-700");
    } else {
        document.getElementById("messageModal").textContent = jsonResponse.message || jsonResponse.error;
        document.getElementById("messageModal").classList.add("text-red-500");
    }

    setTimeout(() => {
        document.getElementById("messageModal").textContent = "";
        // Recargar la página para actualizar la lista
        window.location.reload();
    }, 3000);
}

function openModal() {
    document.getElementById("modal").classList.remove("hidden");

    // Cerrar modal al hacer clic en el floating button (Se convertira en un botón de cerrar)
    const floatingButton = document.getElementById("floatingButton");
    floatingButton.href = "javascript:closeModal()";
    floatingButton.title = "Cerrar modal";
    floatingButton.classList.remove("bg-blue-500", "hover:bg-blue-600");
    floatingButton.classList.add("bg-red-500", "hover:bg-red-600");

    // Cambiar el color de la sombra del floating button y darle una transición suave al cambio
    floatingButton.classList.remove("shadow-[0_0_15px_4px_rgba(59,130,246,0.7)]", "hover:shadow-[0_0_25px_6px_rgba(59,130,246,1)]");
    floatingButton.classList.add("shadow-[0_0_15px_4px_rgba(239,68,68,0.7)]", "hover:shadow-[0_0_25px_6px_rgba(239,68,68,1)]");

    floatingButton.innerHTML = `
        <span class="text-3xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </span>
    `;

    // Cerrar el modal al presionar fuera del mismo
    document.getElementById("modal").addEventListener("click", function(event) {
        if (event.target.id === "modal") {
            closeModal();
        }
    });
}

function closeModal() {
    document.getElementById("modal").classList.add("hidden");

    // Restaurar el floating button
    const floatingButton = document.getElementById("floatingButton");
    floatingButton.href = "javascript:openModal()";
    floatingButton.title = "Crear un QR a partir de texto";
    floatingButton.classList.remove("bg-red-500", "hover:bg-red-600");
    floatingButton.classList.add("bg-blue-500", "hover:bg-blue-600");

    // Restaurar el color de la sombra del floating button y darle una transición suave al cambio
    floatingButton.classList.remove("shadow-[0_0_15px_4px_rgba(239,68,68,0.7)]", "hover:shadow-[0_0_25px_6px_rgba(239,68,68,1)]");
    floatingButton.classList.add("shadow-[0_0_15px_4px_rgba(59,130,246,0.7)]", "hover:shadow-[0_0_25px_6px_rgba(59,130,246,1)]");

    floatingButton.innerHTML = `
        <span class="text-3xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
        </span>
    `;
}

// Ejecutar la funcion getQRs cuando se cargue la página
document.addEventListener("DOMContentLoaded", getQRs);