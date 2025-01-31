async function deletePDF(pdf) {
    if (!confirm("¿Estás seguro de eliminar este archivo?")) {
        return;
    }

    const response = await fetch(`/api/v1/delete/${pdf}`, {
        method: "DELETE"
    });

    const result = await response.json();
    document.getElementById("message").classList.remove("text-green-700", "text-red-500");

    if (response.ok) {
        document.getElementById("message").classList.add("text-green-700");
        document.getElementById("message").textContent = result.message;

        setTimeout(() => {
            document.getElementById("message").textContent = "";
            location.reload(); // Recargar la página para actualizar la lista
        }, 3000);

    } else {
        document.getElementById("message").textContent = result?.message ? result.message : result.error;
        document.getElementById("message").classList.add("text-red-500");

        setTimeout(() => {
            document.getElementById("message").textContent = "";
        }, 3000);
    }
}

async function deleteAllPDFs() {
    if (!confirm("¿Estás seguro de eliminar todos los archivos?")) {
        return;
    }

    const response = await fetch("/api/v1/delete/all", {
        method: "DELETE"
    });

    const result = await response.json();
    document.getElementById("message").classList.remove("text-green-700", "text-red-500");

    if (response.ok) {
        document.getElementById("message").classList.add("text-green-700");
        document.getElementById("message").textContent = result.message;

        setTimeout(() => {
            document.getElementById("message").textContent = "";
            location.reload(); // Recargar la página para actualizar la lista
        }, 3000);

    } else {
        document.getElementById("message").textContent = result?.message ? result.message : result.error;
        document.getElementById("message").classList.add("text-red-500");

        setTimeout(() => {
            document.getElementById("message").textContent = "";
            // Recargar la página para actualizar la lista
            location.reload();
        }, 3000);
    }
}

function viewModal(pdfName) {
    const pdfViewer = document.getElementById("pdfViewer");
    const imageViewer = document.getElementById("imageViewer");
    const textViewer = document.getElementById("textViewer");
    const modalTitle = document.getElementById("modalTitle");

    // Ocultar todos los visores inicialmente
    pdfViewer.classList.add("hidden");
    imageViewer.classList.add("hidden");
    textViewer.classList.add("hidden");

    // Verificar la extension del archivo
    const extension = pdfName.split(".").pop().toLowerCase();
    if (extension === "pdf") {
        pdfViewer.classList.remove("hidden");
        pdfViewer.src = `/api/v1/file/${pdfName}`;
        modalTitle.textContent = "Visor de PDF";
    } else if (extension === "jpg" || extension === "jpeg" || extension === "png" || extension === "gif") {
        imageViewer.classList.remove("hidden");
        imageViewer.src = `/api/v1/file/${pdfName}`;
        modalTitle.textContent = "Visor de imágenes";
    } else {
        textViewer.classList.remove("hidden");
        fetch(`/api/v1/file/${pdfName}`)
            .then(response => response.text())
            .then(data => {
                textViewer.innerHTML = `<span class="text-center text-slate-800 font-bold">${data}</span>`;
            })
            .catch(error => {
                textViewer.innerHTML = `<span class="text-center text-red-500 font-bold">No se pudo cargar el archivo.</span>`;
            });
        modalTitle.textContent = "Visor de texto";
    }

    document.getElementById("pdfModal").classList.remove("hidden"); // Mostrar modal

    // Cerrar modal al hacer clic en el floating button (Se convertira en un botón de cerrar)
    const floatingButton = document.getElementById("floatingButton");
    floatingButton.href = "javascript:closePDF()";
    floatingButton.title = "Cerrar visor";
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
    document.getElementById("pdfModal").addEventListener("click", function(event) {
        if (event.target.id === "pdfModal") {
            closePDF();
        }
    });
}

function closePDF() {
    document.getElementById("pdfModal").classList.add("hidden"); // Ocultar modal
    //document.getElementById("pdfCanvas").getContext("2d").clearRect(0, 0, document.getElementById("pdfCanvas").width, document.getElementById("pdfCanvas").height); // Limpiar canvas
    document.getElementById("pdfViewer").src = ""; // Limpiar iframe
    document.getElementById("imageViewer").src = ""; // Limpiar imagen
    document.getElementById("textViewer").innerHTML = ""; // Limpiar texto

    // Limpiar el titulo del modal
    document.getElementById("modalTitle").textContent = "";

    // Restaurar el floating button
    const floatingButton = document.getElementById("floatingButton");
    floatingButton.href = "/views/upload";
    floatingButton.title = "Subir archivos";
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

async function generateQR(fileName) {
    const response = await fetch(`/api/v1/qr/file/${fileName}`, {
        method: "GET"
    });

    const qr_response = await response.json();

    if (!qr_response.status === 200) {
        alert("No se pudo generar el código QR.");
    }

    document.getElementById("qrImage").src = "/api/v1/qr/" + qr_response.filename; // Mostrar imagen en el modal
    document.getElementById("qrModal").classList.remove("hidden"); // Mostrar modal

    // Cambiar el texto `Generar código QR` por `Ver código QR`
    const qrLink = document.querySelector(`a[data-name="${fileName}"]`);
    qrLink.textContent = "Ver código QR";

    // Cerrar modal al hacer clic en el floating button (Se convertira en un botón de cerrar)
    const floatingButton = document.getElementById("floatingButton");
    floatingButton.href = "javascript:closeQR()";
    floatingButton.title = "Cerrar visor";
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
    document.getElementById("qrModal").addEventListener("click", function(event) {
        if (event.target.id === "qrModal") {
            closeQR();
        }
    });
}

function closeQR() {
    document.getElementById("qrModal").classList.add("hidden"); // Ocultar modal
    document.getElementById("qrImage").src = ""; // Limpiar imagen

    // Restaurar el floating button
    const floatingButton = document.getElementById("floatingButton");
    floatingButton.href = "/views/upload";
    floatingButton.title = "Subir archivos";
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

document.addEventListener("DOMContentLoaded", function() {
    const delButton = document.getElementById("deleteAllButton");

    if (delButton) {
        delButton.addEventListener("click", deleteAllPDFs);
    }
});