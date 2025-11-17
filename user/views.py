from django.shortcuts import render, redirect
#from .forms import UserForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm
from user.models import User 
from .wraps import session_required
import requests

DEFAULT_USER_BONITA = "walter.bates"
url_bonita = "http://localhost:8080/bonita"

# Login en Bonita
def bonita_login(request, bonita_username, bonita_password):
    url = f"{url_bonita}/loginservice"

    payload = {
        "username": bonita_username,
        "password": bonita_password,
        "redirect": "false",
    }

    print(f"Intentando login en Bonita con usuario: {bonita_username} password: {bonita_password}")

    session = requests.Session()
    response = session.post(url, data=payload)
    
    if response.status_code == 204:
        request.session["cookies"] = session.cookies.get_dict()
        request.session["headers"] = {
            "X-Bonita-API-Token": session.cookies.get("X-Bonita-API-Token")
        }
        request.session["username_bonita"] = bonita_username
        print("Login exitoso")
        return session
    else:
        raise Exception("Error al loguearse en Bonita", response.text, response.status_code, response)

# Login de Django
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Usuario no encontrado")
                return redirect("login")
            
            if user.check_password(password):
                # Guardamos en session el login local
                request.session["user_id"] = user.id
                request.session["user_name"] = f"{user.nombre} {user.apellido}"

                # Usamos el username real para Bonita
                bonita_username = user.username
                bonita_password = password

                # Intentamos login en Bonita
                try:
                    bonita_login(request, bonita_username, bonita_password)
                    return render(request, 'home.html', {"user_name": request.session.get("user_name")})
                except Exception as e:
                    print("❌ Error Bonita:", e)
                    messages.error(request, "Error al loguearse en Bonita")
                    return redirect("login")
            else:
                messages.error(request, "Contraseña incorrecta")
    else:
        form = LoginForm()
    
    return render(request, "login.html", {"form": form})
"""
def lista_procesos_disponibles(request):
    procesos = []
    session = request.session.get("cookies")
    if not session:
        return render(request, 'user/lista_procesos.html', {'procesos': procesos})

    # Obtener token
    cookies = request.session.get("cookies", {})
    headers = request.session.get("headers", {})

    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)

    # Endpoint para procesos que el usuario puede iniciar
    url_user_processes = f"{url_bonita}/API/bpm/process?p=0&c=10"

    try:
        response = session.get(url_user_processes, headers=headers, timeout=10)
        response.raise_for_status()
        procesos = response.json()
        print(f"Cantidad de procesos disponibles: {len(procesos)}")
    except requests.exceptions.RequestException as e:
        print("Error al obtener procesos:", e)
        procesos = []

    return render(request, 'user/lista_procesos.html', {'procesos': procesos})
"""

def iniciar_proceso(request, proceso_id):
    if request.method == "POST":
        proceso_id = request.POST.get("proceso_id", proceso_id)

        # Recuperar token y cookies guardadas en la sesión de Django
        cookies = request.session.get("cookies")
        headers = request.session.get("headers")

        if not cookies or not headers:
            print("No hay sesión activa. Debes loguearte primero.")
            return redirect("login")  # redirige al login

        # Crear sesión de requests para reutilizar cookies
        session = requests.Session()
        session.cookies.update(cookies)

        # URL para iniciar el proceso
        url = f"{url_bonita}/API/bpm/process/{proceso_id}/instantiation"

        resp = session.post(url, headers=headers, json={})
        if resp.status_code in [200, 201]:
            data = resp.json()
            print(data)
            case_id = data.get("caseId")
            print("Proceso iniciado, case_id:", case_id)
            # Guardamos el case_id en la sesión o lo pasamos a la siguiente vista
            request.session["case_id"] = case_id
            request.session["proceso_id"] = proceso_id
            # Redirigimos al formulario para llenar datos
            return redirect("llenar_datos_proceso")
        else:
            print("Error al iniciar proceso:", resp.status_code, resp.text)

        return redirect("lista_procesos_disponibles")
    
def llenar_datos_proceso(request):
    case_id = request.session.get("case_id")
    proceso_id = request.session.get("proceso_id")
    cookies = request.session.get("cookies")
    headers = request.session.get("headers")
    username = request.session.get("username_bonita")

    if request.method == "POST":
        datos = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
        }

        session = requests.Session()
        session.cookies.update(cookies)

        url_user = f"{url_bonita}/API/identity/user?f=username={username}"
        user_resp = session.get(url_user, headers=headers)
        if user_resp.status_code != 200 or not user_resp.json():
            print("No se pudo obtener el user_id de Bonita")
            return redirect("lista_procesos_disponibles")

        user_id = user_resp.json()[0]["id"]

        url_tareas = f"{url_bonita}/API/bpm/humanTask?p=0&c=10&f=caseId={case_id}"
        tareas_resp = session.get(url_tareas, headers=headers)
        if tareas_resp.status_code != 200:
            print("Error al obtener tareas:", tareas_resp.text)
            return redirect("lista_procesos_disponibles")

        tareas = tareas_resp.json()
        if not tareas:
            print("No hay tareas disponibles para este caso")
            return redirect("lista_procesos_disponibles")
        

        task = tareas[0]
        task_id = task["id"] 

        if not task.get("assigned_id"):
            url_asignar = f"{url_bonita}/API/bpm/humanTask/{task_id}"
            assign_resp = session.put(url_asignar, headers=headers, json={"assigned_id": user_id})
            print(task_id)
            print(username)
            print(assign_resp)
            print(f"Task assigned")
            if assign_resp.status_code not in [200, 204]:
                print("Error al asignar tarea:", assign_resp.text)
                return redirect("lista_procesos_disponibles")
        print(f"Task id: {task_id}")
        print(username)
        print(user_id)

        debug_resp = f"{url_bonita}/API/bpm/userTask/{task_id}"
        debug_resp = session.get(debug_resp, headers=headers, json=datos)
        print(f"debug response: {debug_resp.text}")

        url_completar = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
        resp = session.post(url_completar, headers=headers, json=datos)
        print(f"Respuesta a execution {resp}")
        if resp.status_code in [200, 204]:
            print("Instancia avanzada con éxito")
            return redirect("lista_procesos_disponibles")
        else:
            print("Error al avanzar instancia:", resp.status_code)
            return redirect("lista_procesos_disponibles")


    return render(request, "user/alta_proyecto.html")

@session_required
def perfil(request):
    # 1️⃣ Verificamos sesión y obtenemos contexto
    from .utils import get_user_context
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")

    return render(request, "perfil.html", user_context)

# cerrar sesion
def logout_view(request):
    request.session.flush()  # elimina toda la sesión
    return redirect('home')
