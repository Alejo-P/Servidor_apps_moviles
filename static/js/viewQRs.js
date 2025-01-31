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
        qrName.setAttribute("class", "text-center text-blue-500 font-bold");
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

// Ejecutar la funcion getQRs cuando se cargue la página
document.addEventListener("DOMContentLoaded", getQRs);