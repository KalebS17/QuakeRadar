import re
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
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
from dotenv import load_dotenv
import os
from .models import Noticia

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


@login_required
def editar_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('name')
        fecha_nacimiento = request.POST.get('birth')
        contrasena = request.POST.get('password')
        user_id = request.user.id  

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC actualizar_usuario @Id=%s, @Nombre=%s, @Contrasena=%s, @FechaNacimiento=%s
                """, [user_id, nombre, contrasena, fecha_nacimiento])
        except Exception as e:
            messages.error(request, f"Error al actualizar perfil: {e}")
            return redirect('user_edit')

        messages.success(request, "Perfil actualizado correctamente.")
        return redirect('user_edit')
    else:
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
    # Actualizar la base de datos de terremotos cada vez que se accede al mapa
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

    if response.status_code == 200:
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
        with connection.cursor() as cursor:
            for eq in earthquakes:
                try:
                    lat = eq["coordinates"][1]
                    lon = eq["coordinates"][0]
                    depth = eq["coordinates"][2]
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
                except Exception as e:
                    print(f"Error al guardar terremoto en mapa: {e}")
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
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Debes ser administrador para acceder al dashboard.")
        return redirect('login')
    with connection.cursor() as cursor:
        cursor.execute("SELECT Id, Nombre, Correo FROM Usuarios")
        usuarios = [
            {"id": row[0], "name": row[1], "email": row[2], "fuente": "Usuarios"}
            for row in cursor.fetchall()
        ]

    auth_users = User.objects.all().values("id", "first_name", "email")
    auth_users_list = [
        {"id": u["id"], "name": u["first_name"], "email": u["email"], "fuente": "auth_user"}
        for u in auth_users
    ]

    usuarios_dict = {u["email"]: u for u in usuarios}
    for u in auth_users_list:
        if u["email"] and u["email"] not in usuarios_dict:
            usuarios_dict[u["email"]] = u
    all_users = list(usuarios_dict.values())

    noticias = Noticia.objects.all().order_by('-fecha_publicacion')
    return render(request, 'admin_dashboard.html', {"visiting_users": all_users, "noticias": noticias})


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

    saved_count = 0
    with connection.cursor() as cursor:
        for eq in earthquakes:
            try:
                # USGS: [longitud, latitud, profundidad]
                lat = eq["coordinates"][1]
                lon = eq["coordinates"][0]
                depth = eq["coordinates"][2]
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
            except Exception as e:
                print(f"Error al guardar terremoto: {e}")
    return HttpResponse(f"{saved_count} terremotos guardados correctamente.")

# Punto 2: Obtener terremotos aleatorios de la base de datos
def get_random_earthquakes_db():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT TOP 50 latitud, longitud, magnitud, profundidad, fecha_hora
            FROM dbo.Terremoto
            ORDER BY NEWID()
        """)
        rows = cursor.fetchall()
    sample = random.sample(rows, min(7, len(rows)))
    terremotos = [
        {
            "latitud": row[0],
            "longitud": row[1],
            "magnitud": row[2],
            "profundidad": row[3],
            "fecha_hora": row[4],
        }
        for row in sample
    ]
    return terremotos


def generar_noticia(terremoto):
    mag = terremoto['magnitud']
    autores = [
        "Redacción QuakeRadar",
        "Agencia Sísmica Nacional",
        "Reporte Especial",
        "Equipo de Noticias",
        "Observatorio Sismológico",
        "Corresponsal Local",
        "Centro de Monitoreo"
    ]
    autor = random.choice(autores)
    # Generar fecha de publicación aleatoria (entre 1 minuto y 48 horas después del incidente)
    fecha_incidente = terremoto['fecha_hora']
    if isinstance(fecha_incidente, str):
        try:
            fecha_incidente = datetime.fromisoformat(str(fecha_incidente))
        except Exception:
            fecha_incidente = datetime.now()
    min_offset = timedelta(minutes=1)
    max_offset = timedelta(hours=48)
    offset = min_offset + (max_offset - min_offset) * random.random()
    fecha_publicacion = fecha_incidente + offset
    fecha_publicacion_str = fecha_publicacion.strftime('%Y-%m-%d %H:%M')
    if mag < 3.0:
        titulos = [
            f"Sismo leve registrado (Magnitud {mag})",
            f"Pequeño temblor detectado en la región (Mag. {mag})",
            f"Movimiento sísmico menor sin afectaciones (Mag. {mag})"
        ]
        cuerpos = [
            f"Un sismo de baja magnitud ({mag}) fue detectado el {terremoto['fecha_hora']}. El epicentro estuvo en latitud {terremoto['latitud']}, longitud {terremoto['longitud']}, a {terremoto['profundidad']} km de profundidad. No se reportan daños ni afectaciones.",
            f"Se registró un temblor leve de magnitud {mag} el {terremoto['fecha_hora']}. El evento pasó desapercibido para la mayoría de la población.",
            f"Un pequeño sismo ocurrió el {terremoto['fecha_hora']} con epicentro en latitud {terremoto['latitud']}, longitud {terremoto['longitud']}. Sin consecuencias para la comunidad. Magnitud reportada: {mag}."
        ]
    elif mag < 5.0:
        titulos = [
            f"Terremoto moderado sacude la zona (Magnitud {mag})",
            f"Sismo de magnitud intermedia sorprende a habitantes (Mag. {mag})",
            f"Temblor causa inquietud en la comunidad (Mag. {mag})"
        ]
        cuerpos = [
            f"Un terremoto de magnitud {mag} se registró el {terremoto['fecha_hora']}. El epicentro estuvo en latitud {terremoto['latitud']}, longitud {terremoto['longitud']}, a {terremoto['profundidad']} km de profundidad. Se sintió en varias comunidades, pero no se reportan daños graves.",
            f"El {terremoto['fecha_hora']} se produjo un sismo de magnitud {mag} que generó inquietud entre los habitantes locales.",
            f"Un temblor moderado sacudió la zona el {terremoto['fecha_hora']}, sin consecuencias graves reportadas. Magnitud registrada: {mag}."
        ]
    elif mag < 7.0:
        titulos = [
            f"Fuerte sismo genera alarma (Magnitud {mag})",
            f"Terremoto intenso sacude la región (Mag. {mag})",
            f"Sismo de gran magnitud alerta a la población (Mag. {mag})"
        ]
        cuerpos = [
            f"Un fuerte terremoto de magnitud {mag} sacudió la región el {terremoto['fecha_hora']}. El epicentro estuvo en latitud {terremoto['latitud']}, longitud {terremoto['longitud']}, a {terremoto['profundidad']} km de profundidad. Las autoridades recomiendan precaución ante posibles réplicas.",
            f"El {terremoto['fecha_hora']} se registró un sismo de gran magnitud ({mag}) que generó alarma en la población.",
            f"Un terremoto intenso fue percibido el {terremoto['fecha_hora']}, con epicentro en latitud {terremoto['latitud']}, longitud {terremoto['longitud']}. Magnitud: {mag}."
        ]
    else:
        titulos = [
            f"Terremoto devastador impacta el área (Magnitud {mag})",
            f"Sismo de extrema magnitud causa daños significativos (Mag. {mag})",
            f"Evento sísmico mayor afecta la región (Mag. {mag})"
        ]
        cuerpos = [
            f"Un terremoto de gran magnitud ({mag}) ocurrió el {terremoto['fecha_hora']}. El epicentro estuvo en latitud {terremoto['latitud']}, longitud {terremoto['longitud']}, a {terremoto['profundidad']} km de profundidad. Se reportan daños significativos y se recomienda seguir las indicaciones de las autoridades.",
            f"El {terremoto['fecha_hora']} se produjo un sismo devastador de magnitud {mag}, con afectaciones en varias zonas.",
            f"Un evento sísmico mayor sacudió la región el {terremoto['fecha_hora']}, generando preocupación y daños materiales. Magnitud: {mag}."
        ]
    titulo = random.choice(titulos)
    cuerpo = random.choice(cuerpos)
    return {"titulo": titulo, "autor": autor, "cuerpo": cuerpo, "fecha_publicacion": fecha_publicacion_str}

def procesar_noticia(noticia_texto):
    partes = noticia_texto.split('\n')
    titulo = partes[0] if len(partes) > 0 else "Título no disponible"
    autor = partes[1] if len(partes) > 1 else "Autor no disponible"
    cuerpo = "\n".join(partes[2:]) if len(partes) > 2 else ""
    return {"titulo": titulo, "autor": autor, "cuerpo": cuerpo}

def news_generator(request):
    pass  # (bloque vacío para evitar error de indentación)
# --- Vistas para editar y eliminar noticias ---
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_edit_news(request, noticia_id):
    noticia = get_object_or_404(Noticia, id=noticia_id)
    if request.method == 'POST':
        noticia.titulo = request.POST.get('titulo')
        noticia.autor = request.POST.get('autor')
        noticia.cuerpo = request.POST.get('cuerpo')
        fecha_str = request.POST.get('fecha_publicacion')
        try:
            noticia.fecha_publicacion = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
        except Exception:
            pass
        noticia.save()
        messages.success(request, 'Noticia actualizada correctamente.')
        return redirect('admin_dashboard')
    return render(request, 'admin_edit_news.html', {'noticia': noticia})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_delete_news(request, noticia_id):
    noticia = get_object_or_404(Noticia, id=noticia_id)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada correctamente.')
        return redirect('admin_dashboard')
    return render(request, 'admin_dashboard.html')
    terremotos = get_random_earthquakes_db()
    if not terremotos:
        return render(request, "news.html", {"noticias": [], "mensaje": "No hay terremotos en la base de datos."})
    noticias = []
    for t in terremotos:
        noticia_data = generar_noticia(t)
        # Convertir fecha_publicacion a datetime si es string
        fecha_pub = noticia_data["fecha_publicacion"]
        if isinstance(fecha_pub, str):
            try:
                fecha_pub_dt = datetime.strptime(fecha_pub, "%Y-%m-%d %H:%M")
            except Exception:
                fecha_pub_dt = datetime.now()
        else:
            fecha_pub_dt = fecha_pub
        noticia_obj, created = Noticia.objects.get_or_create(
            titulo=noticia_data["titulo"],
            autor=noticia_data["autor"],
            cuerpo=noticia_data["cuerpo"],
            fecha_publicacion=fecha_pub_dt
        )
        noticias.append(noticia_data)
    return render(request, "news.html", {"noticias": noticias})

from django.views.decorators.http import require_POST

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eliminar_usuario(request, user_id, fuente):
    if fuente == 'Usuarios':
        try:
            with connection.cursor() as cursor:
                cursor.execute("EXEC eliminar_usuario @Id=%s", [user_id])
            messages.success(request, "Usuario eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar usuario: {e}")
    elif fuente == 'auth_user':
        try:
            User.objects.filter(id=user_id).delete()
            messages.success(request, "Usuario eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar usuario: {e}")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def editar_usuario_admin(request, user_id, fuente):
    if fuente == 'Usuarios':
        if request.method == 'POST':
            nombre = request.POST.get('name')
            fecha_nacimiento = request.POST.get('birth')
            contrasena = request.POST.get('password')
            try:
                with connection.cursor() as cursor:
                    cursor.execute("EXEC actualizar_usuario @Id=%s, @Nombre=%s, @Contrasena=%s, @FechaNacimiento=%s", [user_id, nombre, contrasena, fecha_nacimiento])
                messages.success(request, "Usuario actualizado correctamente.")
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f"Error al actualizar usuario: {e}")
        else:
            # Obtener datos actuales
            with connection.cursor() as cursor:
                cursor.execute("SELECT Nombre, FechaNacimiento FROM Usuarios WHERE Id=%s", [user_id])
                row = cursor.fetchone()
            return render(request, 'admin_edit_user.html', {
                'user_id': user_id,
                'fuente': fuente,
                'nombre': row[0] if row else '',
                'fecha_nacimiento': row[1].strftime('%Y-%m-%d') if row and row[1] else '',
            })
    elif fuente == 'auth_user':
        if request.method == 'POST':
            nombre = request.POST.get('name')
            fecha_nacimiento = request.POST.get('birth')
            contrasena = request.POST.get('password')
            try:
                user = User.objects.get(id=user_id)
                user.first_name = nombre
                user.set_password(contrasena)
                user.save()
                # Guardar fecha de nacimiento en un campo extra si lo tienes (ejemplo: user.profile.birthdate)
                # Si tienes un modelo Profile relacionado, descomenta y ajusta:
                # user.profile.birthdate = fecha_nacimiento
                # user.profile.save()
                messages.success(request, "Usuario actualizado correctamente.")
                return redirect('admin_dashboard')
            except Exception as e:
                messages.error(request, f"Error al actualizar usuario: {e}")
        else:
            user = User.objects.get(id=user_id)
            # Si tienes un campo extra para fecha de nacimiento, pásalo aquí
            return render(request, 'admin_edit_user.html', {
                'user_id': user_id,
                'fuente': fuente,
                'nombre': user.first_name,
                'fecha_nacimiento': '',  # Ajusta si tienes el campo
            })