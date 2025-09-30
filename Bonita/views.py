from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests

# Configuración Bonita
url_bonita = "http://localhost:8080/bonita"
user = "walter.bates"
password = "admin"

# --------------------------
# LOGIN
# --------------------------
def bonita_login(request):
    url = f"{url_bonita}/loginservice"
    payload = {
        "username": user,
        "password": password,
        "redirect": "false",
    }

    session = requests.Session()
    response = session.post(url, data=payload)

    if response.status_code == 204:
        request.session["cookies"] = session.cookies.get_dict()
        request.session["headers"] = {
            "X-Bonita-API-Token": session.cookies.get("X-Bonita-API-Token")
        }
        request.session["username_bonita"] = user
        return session
    else:
        raise Exception("Error al loguearse en Bonita", response.text)

# --------------------------
# LISTA DE PROCESOS
# --------------------------
def lista_procesos_disponibles(request):
    procesos = []
    try:
        session = bonita_login(request)
    except Exception:
        return render(request, 'bonita/lista_procesos.html', {'procesos': procesos})

    cookies = request.session.get("cookies", {})
    headers = request.session.get("headers", {})

    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)

    url_user_processes = f"{url_bonita}/API/bpm/process?p=0&c=10"
    try:
        response = session.get(url_user_processes, headers=headers, timeout=10)
        response.raise_for_status()
        procesos = response.json()
    except requests.exceptions.RequestException:
        procesos = []

    return render(request, 'bonita/lista_procesos.html', {'procesos': procesos})

# --------------------------
# INICIAR PROCESO
# --------------------------
def iniciar_proceso(request, proceso_id):
    if request.method == "POST":
        proceso_id = request.POST.get("proceso_id", proceso_id)

        cookies = request.session.get("cookies")
        headers = request.session.get("headers")

        if not cookies or not headers:
            return redirect("bonita:lista_procesos")

        session = requests.Session()
        session.cookies.update(cookies)

        url = f"{url_bonita}/API/bpm/process/{proceso_id}/instantiation"
        resp = session.post(url, headers=headers, json={})

        if resp.status_code in [200, 201]:
            data = resp.json()
            case_id = data.get("caseId")
            request.session["case_id"] = case_id
            request.session["proceso_id"] = proceso_id
            return redirect("bonita:llenar_datos_proceso")

    return redirect("bonita:lista_procesos")

# --------------------------
# LLENAR DATOS DE PROCESO
# --------------------------
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

        # Obtener user_id de Bonita
        url_user = f"{url_bonita}/API/identity/user?f=username={username}"
        user_resp = session.get(url_user, headers=headers)
        if user_resp.status_code != 200 or not user_resp.json():
            return redirect("bonita:lista_procesos")

        user_id = user_resp.json()[0]["id"]

        # Obtener tareas del caso
        url_tareas = f"{url_bonita}/API/bpm/humanTask?p=0&c=10&f=caseId={case_id}"
        tareas_resp = session.get(url_tareas, headers=headers)
        if tareas_resp.status_code != 200:
            return redirect("bonita:lista_procesos")

        tareas = tareas_resp.json()
        if not tareas:
            return redirect("bonita:lista_procesos")

        task = tareas[0]
        task_id = task["id"]

        # Asignar tarea si no está asignada
        if not task.get("assigned_id"):
            url_asignar = f"{url_bonita}/API/bpm/humanTask/{task_id}"
            assign_resp = session.put(url_asignar, headers=headers, json={"assigned_id": user_id})
            if assign_resp.status_code not in [200, 204]:
                return redirect("bonita:lista_procesos")

        # Completar tarea
        url_completar = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
        resp = session.post(url_completar, headers=headers, json=datos)
        if resp.status_code in [200, 201]:
            return redirect("bonita:lista_procesos")

    return render(request, "bonita/alta_proyecto.html")
