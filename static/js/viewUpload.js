document.getElementById("uploadForm").addEventListener("submit", async function(event) {
    event.preventDefault(); // Evita que la página se recargue

    const formData = new FormData();
    const fileInput = document.getElementById("fileInput");
    
    if (fileInput.files.length === 0) {
        alert("Selecciona un archivo antes de subir.");
        return;
    }

    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("/api/v1/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log(result);
        document.getElementById("message").classList.remove("text-green-700", "text-red-500");

        if (response.ok) {
            document.getElementById("message").classList.add("text-green-700");
            document.getElementById("message").textContent = result.message;
        } else {
            document.getElementById("message").textContent = result?.message ? result.message : result.error;
            document.getElementById("message").classList.add("text-red-500");
        }
    } catch (error) {
        document.getElementById("message").textContent = error.message;
        document.getElementById("message").classList.add("text-red-500");
    } finally {
        fileInput.value = "";
        setTimeout(() => {
            document.getElementById("message").textContent = "";
        }, 3000);
    }
});

// Ocultar el mensaje cuando se seleccione un archivo
document.getElementById("fileInput").addEventListener("change", function() {
    document.getElementById("message").textContent = "";
    document.getElementById("message").classList.remove("text-green-700", "text-red-500");
});