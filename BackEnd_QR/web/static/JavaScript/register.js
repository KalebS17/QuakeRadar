// Script para la barra de fuerza de contraseña y criterios
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".register-form");
    const inputs = form.querySelectorAll("input");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirm-password");
    const strengthBar = document.getElementById("strength-bar");
    const strengthText = document.getElementById("strength-text");

    const criteriaLength = document.getElementById("criteria-length");
    const criteriaUppercase = document.getElementById("criteria-uppercase");
    const criteriaLowercase = document.getElementById("criteria-lowercase");
    const criteriaNumber = document.getElementById("criteria-number");
    const criteriaSpecial = document.getElementById("criteria-special");

    function isOnlyLetters(str) {
        return /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(str);
    }

    function isOnlyNumbers(str) {
        return /^\d+$/.test(str);
    }

    confirmPasswordInput.addEventListener("input", () => {
    confirmPasswordInput.setCustomValidity("");
    confirmPasswordInput.classList.remove("error");
    });

    passwordInput.addEventListener("input", () => {
    confirmPasswordInput.setCustomValidity("");
    confirmPasswordInput.classList.remove("error");
    });
    
    form.addEventListener("submit", (event) => {
        let isValid = true;

        inputs.forEach((input) => {
            const value = input.value.trim();

            // Verifica si el campo está vacío
            if (!value) {
                isValid = false;
                input.classList.add("error");
                input.setCustomValidity("Este campo no puede estar vacío.");
            } else {
                input.classList.remove("error");
                input.setCustomValidity("");
            }

            // Solo sanitiza si NO es password
            if (input.type !== "password") {
                input.value = sanitizeInput(value);
            }
        });

        // Validar nombre y apellidos
        const nameValue = document.getElementById("name").value.trim();
        const surnameValue = document.getElementById("surname").value.trim();
        if (!isOnlyLetters(nameValue)) {
            isValid = false;
            alert("El nombre solo puede contener letras y espacios.");
        }
        if (!isOnlyLetters(surnameValue)) {
            isValid = false;
            alert("El apellido solo puede contener letras y espacios.");
        }

        // Validar teléfono
        const phoneValue = document.getElementById("phone").value.trim();
        if (!isOnlyNumbers(phoneValue)) {
            isValid = false;
            alert("El teléfono solo puede contener números.");
        }

        // Verifica que las contraseñas sean iguales
        const passwordValue = passwordInput.value.trim();
        const confirmPasswordValue = confirmPasswordInput.value.trim();

        if (passwordValue !== confirmPasswordValue) {
            isValid = false;
            confirmPasswordInput.classList.add("error");
            confirmPasswordInput.setCustomValidity("Las contraseñas no coinciden.");
            alert("Las contraseñas no coinciden.");
        } else {
            confirmPasswordInput.classList.remove("error");
            confirmPasswordInput.setCustomValidity("");
        }

        if (!isValid) {
            event.preventDefault(); // Evita el envío del formulario si hay errores
            alert("Por favor, corrige los errores antes de continuar.");
        }
    });

    // Función para sanitizar el valor del campo
    function sanitizeInput(value) {
        return value.replace(/<[^>]*>?/gm, ""); // Elimina cualquier etiqueta HTML
    }

    passwordInput.addEventListener("input", () => {
        const password = passwordInput.value;

        // Verifica los criterios
        const hasLength = password.length >= 8;
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        // Actualiza los criterios visualmente
        criteriaLength.style.color = hasLength ? "green" : "red";
        criteriaUppercase.style.color = hasUppercase ? "green" : "red";
        criteriaLowercase.style.color = hasLowercase ? "green" : "red";
        criteriaNumber.style.color = hasNumber ? "green" : "red";
        criteriaSpecial.style.color = hasSpecial ? "green" : "red";

        // Calcula la fuerza de la contraseña
        const criteriaMet = [hasLength, hasUppercase, hasLowercase, hasNumber, hasSpecial].filter(Boolean).length;

        if (criteriaMet === 0) {
            strengthBar.style.width = "20%";
            strengthBar.style.backgroundColor = "#e9ecef";
            strengthText.textContent = "Seguridad: baja";
        } else if (criteriaMet <= 2) {
            strengthBar.style.width = "40%";
            strengthBar.style.backgroundColor = "#ef233c"; // rojo
            strengthText.textContent = "Seguridad: baja";
        } else if (criteriaMet <= 4) {
            strengthBar.style.width = "70%";
            strengthBar.style.backgroundColor = "#fbbf24"; // amarillo
            strengthText.textContent = "Seguridad: media";
        } else {
            strengthBar.style.width = "100%";
            strengthBar.style.backgroundColor = "#a0f1bd"; // verde
            strengthText.textContent = "Seguridad: alta";
        }
    });

    // Script para el botón de mostrar/ocultar contraseña
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
});

