import re
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from datetime import datetime, timedelta, timezone
import requests
from django.http import JsonResponse
from django.http import HttpResponse
import random


def index(request):
    return render(request, 'index.html')

#Funcion para cerrar sesión
def logout_view(request):
    request.session.flush()  # Elimina todos los datos de la sesión
    return redirect('index')  # Redirige a la página de inicio o a donde desees

#FUNCION PARA INICIAR SESION
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # 1. Busca en Usuarios
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Id, Nombre FROM Usuarios WHERE Correo = %s AND Contraseña = %s
            """, [email, password])
            row = cursor.fetchone()

        if row:
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'first_name': row[1], 'email': email}
            )
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            return redirect('login_exitoso')

        # 2. Si no está en Usuarios, busca en admin
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Id, Nombre FROM admin WHERE Correo = %s AND Contraseña = %s
            """, [email, password])
            admin_row = cursor.fetchone()

        if admin_row:
            # Puedes usar un username especial para distinguir admins
            admin_username = f"admin_{email}"
            user, created = User.objects.get_or_create(
                username=admin_username,
                defaults={'first_name': admin_row[1], 'email': email, 'is_staff': True, 'is_superuser': True}
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            return redirect('admin_dashboard')  # O la página que quieras para admins

        # Si no está en ninguna tabla
        messages.error(request, "Correo o contraseña incorrectos.")
    return render(request, 'logIn.html')


def login_exitoso(request):
    return render(request, 'logInExitoso.html')

@login_required
def user_edit(request):
    return render(request, 'UserEdit.html')

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

def mapa(request):
    return render(request, 'Mapa.html')



#funcion para obtener los datos de la API de terremotos
def fetch_earthquake_data(request):
    # Zona horaria de Costa Rica (UTC-6)
    tz_costa_rica = timezone(timedelta(hours=-6))

    # Hora actual en Costa Rica
    costarica_now = datetime.now(tz_costa_rica)
    now_utc = costarica_now.astimezone(timezone.utc)

    # Formato ISO8601 para la API
    endtime = now_utc.isoformat(timespec='seconds').replace('+00:00', 'Z')
    starttime = (now_utc - timedelta(days=1)).isoformat(timespec='seconds').replace('+00:00', 'Z')

    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
    }

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        # Extraer los datos relevantes para el mapa
        earthquakes = [
            {
                "id": feature["id"],
                "mag": feature["properties"]["mag"],
                "place": feature["properties"]["place"],
                "type": feature["properties"]["type"],
                "time": feature["properties"]["time"],
                "coordinates": feature["geometry"]["coordinates"],
            }
            for feature in data["features"] #usamos list comprehension
        ]
        return JsonResponse({"earthquakes": earthquakes})
    else:
        return JsonResponse({"error": f"Error al consultar la API: {response.status_code}"}, status=500)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard(request):
    # Usuarios de la tabla Usuarios
    with connection.cursor() as cursor:
        cursor.execute("SELECT Id, Nombre, Correo FROM Usuarios")
        usuarios = [
            {"id": row[0], "name": row[1], "email": row[2]}
            for row in cursor.fetchall()
        ]

    # Usuarios de auth_user
    auth_users = User.objects.all().values("id", "first_name", "email")
    auth_users_list = [
        {"id": u["id"], "name": u["first_name"], "email": u["email"]}
        for u in auth_users
    ]

    # Unir ambas listas
    all_users = usuarios + auth_users_list

    return render(request, 'admin_dashboard.html', {"visiting_users": all_users})


#Funcion para Guardar Terremotos en la DB
def save_earthquake_data(request):
    # Zona horaria de Costa Rica
    tz_costa_rica = timezone(timedelta(hours=-6))
    costarica_now = datetime.now(tz_costa_rica)
    now_utc = costarica_now.astimezone(timezone.utc)

    endtime = now_utc.isoformat(timespec='seconds').replace('+00:00', 'Z')
    starttime = (now_utc - timedelta(days=1)).isoformat(timespec='seconds').replace('+00:00', 'Z')

    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
    }

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return HttpResponse(f"Error al consultar la API: {response.status_code}", status=500)

    data = response.json()
    earthquakes = [
        {
            "id": feature["id"],
            "mag": feature["properties"]["mag"],
            "place": feature["properties"]["place"],
            "type": feature["properties"]["type"],
            "time": feature["properties"]["time"],
            "coordinates": feature["geometry"]["coordinates"],
        }
        for feature in data["features"]
    ]

    sample = random.sample(earthquakes, min(7, len(earthquakes)))

    saved_count = 0

    with connection.cursor() as cursor:
        for eq in sample:
            lon, lat, depth = eq["coordinates"]
            mag = eq["mag"]
            time = datetime.utcfromtimestamp(eq["time"] / 1000)

            cursor.execute("""
                SELECT COUNT(*) FROM dbo.Terremoto
                WHERE latitud = %s AND longitud = %s AND fecha_hora = %s
            """, [lat, lon, time])
            exists = cursor.fetchone()[0]

            if exists == 0:
                cursor.execute("""
                    INSERT INTO dbo.Terremoto (latitud, longitud, magnitud, profundidad, fecha_hora)
                    VALUES (%s, %s, %s, %s, %s)
                """, [lat, lon, mag, depth, time])
                saved_count += 1

    return HttpResponse(f"{saved_count} terremotos guardados correctamente.")


def news_generator(request):
    return render(request, 'news.html')

