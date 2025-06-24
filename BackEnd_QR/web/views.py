import re
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages


def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'logIn.html')

def register(request):
    return render(request, 'register.html')

def login_exitoso(request):
    return render(request, 'logInExitoso.html')

def user_edit(request):
    return render(request, 'userEdit.html')

#Llamar al store procedure para registrar un usuario
def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        surnames = request.POST.get('surname', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        birthdate = request.POST.get('birthdate', '').strip()

        # Validación de solo letras y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', name):
            messages.error(request, "El nombre solo puede contener letras y espacios.")
            return render(request, 'register.html')
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', surnames):
            messages.error(request, "El apellido solo puede contener letras y espacios.")
            return render(request, 'register.html')
        # Validación de solo números en teléfono
        if not re.match(r'^\d+$', phone):
            messages.error(request, "El teléfono solo puede contener números.")
            return render(request, 'register.html')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC insertar_usuario @Nombre=%s, @Apellidos=%s, @Correo=%s, @Telefono=%s, @Contrasena=%s, @FechaNacimiento=%s
                """, [name, surnames, email, phone, password, birthdate])
            messages.success(request, "Usuario registrado correctamente.")
            return redirect('login')
        except Exception as e:
            if 'duplicate key' in str(e).lower():
                messages.error(request, "El correo o teléfono ya están registrados.")
            else:
                messages.error(request, f"Error al registrar usuario: {e}")

    # Para GET (cuando solo visitas la página)
    return render(request, 'register.html')

