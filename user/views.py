from django.shortcuts import render, redirect
from .forms import UserForm
from django.http import JsonResponse
import requests

url_bonita = "http://localhost:8080/bonita"
user = "walter.bates"
password = "admin"

def alta_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_users')  # Redirige a otra vista (por ejemplo, lista)
    else:
        form = UserForm()
    return render(request, 'User/altas_users.html', {'form': form})

def bonita_login(request):
    url = f"{url_bonita}/loginservice"
    payload = {
        "username": user,
        "password": password,
        "redirect": "false",
    }

    session = requests.Session()
    response = session.post(url, data=payload)
    print("STATUS:", response.status_code)
    print("COOKIES:", session.cookies.get_dict())
    print("BODY:", response.text)
    if response.status_code == 204:
        request.session["cookies"] = session.cookies.get_dict()
        request.session["headers"] = {
            "X-Bonita-API-Token": session.cookies.get("X-Bonita-API-Token")
        }
        request.session["username_bonita"] = user
        print("Login exitoso")
        return session
    else:
        raise Exception("Error al loguearse en Bonita", response.text)
    
def lista_procesos_disponibles(request):
    procesos = []
    session = bonita_login(request)
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
            if assign_resp.status_code not in [200, 204]:
                print("Error al asignar tarea:", assign_resp.text)
                return redirect("lista_procesos_disponibles")
        print(task_id)
        print(username)
        print(user_id)
        print(username)
        url_completar = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
        resp = session.post(url_completar, headers=headers, json=datos)
        if resp.status_code in [200, 201]:
            print("Instancia avanzada con éxito")
            return redirect("lista_procesos_disponibles")
        else:
            print("Error al avanzar instancia:", resp.status_code)
            return redirect("lista_procesos_disponibles")


    return render(request, "user/alta_proyecto.html")