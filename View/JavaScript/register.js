// Script para la barra de fuerza de contraseña
document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("password");
    const strengthBar = document.getElementById("strength-bar");
    const strengthText = document.getElementById("strength-text");

    passwordInput.addEventListener("input", () => {
        const password = passwordInput.value;
        const length = password.length;

        if (length === 0) {
            strengthBar.style.width = "20%";
            strengthBar.style.backgroundColor = "#e9ecef";
            strengthText.textContent = "Seguridad: baja";
        } else if (length < 8) {
            strengthBar.style.width = "40%";
            strengthBar.style.backgroundColor = "#ef233c"; // rojo
            strengthText.textContent = "Seguridad: baja";
        } else if (length < 12) {
            strengthBar.style.width = "70%";
            strengthBar.style.backgroundColor = "#fbbf24"; // amarillo
            strengthText.textContent = "Seguridad: media";
        } else {
            strengthBar.style.width = "100%";
            strengthBar.style.backgroundColor = "#4cc9f0"; // azul (buena seguridad)
            strengthText.textContent = "Seguridad: alta";
        }
    });
});

// Script para el botón de mostrar/ocultar contraseña
document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("password");
    const togglePasswordBtn = document.querySelector(".toggle-password");
    const eyeIcon = togglePasswordBtn.querySelector("i");

    togglePasswordBtn.addEventListener("click", () => {
        const isPasswordVisible = passwordInput.type === "text";

        // Cambia el tipo de input
        passwordInput.type = isPasswordVisible ? "password" : "text";

        // Cambia el ícono del ojo
        eyeIcon.classList.toggle("fa-eye");
        eyeIcon.classList.toggle("fa-eye-slash");
    });

    // ... Aquí puedes poner el código de fuerza de contraseña también (ya lo tienes arriba)
});
