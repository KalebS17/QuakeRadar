document.addEventListener('DOMContentLoaded', () => {
    const circle = document.querySelector('.success-circle');
    
    // Añadir clase para animación continua después del efecto inicial
    setTimeout(() => {
        circle.classList.add('animated');
    }, 1500);
});