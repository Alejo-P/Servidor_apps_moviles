async function getQRs() {
    const response = await fetch('/api/v1/qrs', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    data = await response.json();

    const qrArray = data.files;
    let delButton = document.getElementById("deleteAllButton");

    let qrDivPrincipal = document.getElementById("QRs");

    //Remover estilos de flexbox y grid
    qrDivPrincipal.classList.remove("flex", "flex-col", "items-center", "justify-center");
    qrDivPrincipal.classList.remove("grid", "grid-cols-1", "md:grid-cols-2", "lg:grid-cols-3", "xl:grid-cols-4", "gap-4");

    if (qrArray.length > 0) {
        delButton.classList.remove("hidden");
        delButton.addEventListener("click", deleteAllQRs);

        qrDivPrincipal.classList.add("grid", "grid-cols-1", "md:grid-cols-2", "lg:grid-cols-3", "xl:grid-cols-4", "gap-4");
    } else {
        delButton.classList.add("hidden");

        qrDivPrincipal.classList.add("flex", "flex-col", "items-center", "justify-center");
        let noQRs = document.createElement("p");
        noQRs.textContent = "No hay QRs disponibles";
        noQRs.setAttribute("class", "text-center text-gray-500 w-full h-48 flex items-center justify-center");
        qrDivPrincipal.appendChild(noQRs);
    }

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

        let buttons = document.createElement("div");
        buttons.setAttribute("class", "flex justify-center space-x-4 mt-4");
        qrDiv.appendChild(buttons);

        let downloadButton = document.createElement("button");
        downloadButton.setAttribute("class", "bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline");
        downloadButton.setAttribute("title", "Descargar QR");
        downloadButton.innerHTML = `
            <span class="text-3xl">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v12m0 0l-6-6m6 6l6-6M4 20h16"/>
                </svg>
            </span>
        `;
        downloadButton.addEventListener("click", async () => {
            const response = await downloadQR(qr);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = qr;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        });
        buttons.appendChild(downloadButton);

        let deleteButton = document.createElement("button");
        deleteButton.setAttribute("class", "bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline");
        deleteButton.setAttribute("title", "Eliminar QR");
        deleteButton.innerHTML = `
            <span class="text-3xl">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </span>
        `;
        deleteButton.addEventListener("click", async () => {
            deleteQR(qr);
        });
        buttons.appendChild(deleteButton);

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
    if (!confirm(`¿Estás seguro de que deseas eliminar el QR ${name}?`)) {
        return;
    }

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
        // Recargar la página para actualizar la lista
        window.location.reload();
    }, 3000);
}

async function deleteAllQRs() {
    if (!confirm("¿Estás seguro de que deseas eliminar todos los QRs?")) {
        return;
    }

    const response = await fetch('/api/v1/qrs', {
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
        // Recargar la página para actualizar la lista
        window.location.reload();
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
    let text = document.getElementById("QRtext").value.trim();
    let icon = document.getElementById("QRicon").files[0];

    let messageModal = document.getElementById("messageModal");

    // Validar que el texto no esté vacío
    if (!text) {
        messageModal.textContent = "El campo de texto no puede estar vacío";
        messageModal.classList.add("text-red-500");
        
        setTimeout(() => {
            messageModal.textContent = "";
            messageModal.classList.remove("text-red-500");
        }, 3000);
        return;
    }

    // Crear FormData y agregar los datos
    const formData = new FormData();
    formData.append("text", text);
    if (icon) {
        formData.append("icon", icon);
    }

    try {
        const response = await fetch('/api/v1/qr', {
            method: 'POST',
            body: formData
        });
        const jsonResponse = await response.json();

        messageModal.classList.remove("text-green-700", "text-red-500");

        if (response.ok) {
            messageModal.textContent = jsonResponse.message;
            messageModal.classList.add("text-green-700");
        } else {
            messageModal.textContent = jsonResponse.message || jsonResponse.error;
            messageModal.classList.add("text-red-500");
        }
    } catch (error) {
        console.error(error);

        messageModal.textContent = "Ocurrió un error al crear el QR";
        messageModal.classList.add("text-red-500");
    } finally {
        document.getElementById("QRtext").value = "";
        document.getElementById("QRicon").value = "";

        setTimeout(() => {
            messageModal.textContent = "";
            if (messageModal.classList.contains("text-green-700")) {
                // Recargar la página para actualizar la lista
                location.reload();
            }
        }, 3000);
    }
}

function openModal() {
    document.getElementById("modal").classList.remove("hidden");
    document.getElementById("backButton").classList.add("hidden");

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
    document.getElementById("backButton").classList.remove("hidden");

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