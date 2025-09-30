from django.shortcuts import render, redirect
from Bonita import url_bonita
import requests



def llenar_datos_proceso(request):
    case_id = request.session.get("case_id")
    proceso_id = request.session.get("proceso_id")
    cookies = request.session.get("cookies")
    headers = request.session.get("headers")

    if request.method == "POST":
        # Aquí tomamos los datos del formulario
        datos = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
            # agregá más campos según tu proceso
        }

        # Avanzar la instancia usando API de tareas (human tasks)
        session = requests.Session()
        session.cookies.update(cookies)

        # Primero obtenemos la tarea asignada a este case
        url_tareas = f"{url_bonita}/API/bpm/humanTask?p=0&c=10&f=caseId={case_id}"
        tareas_resp = session.get(url_tareas, headers=headers)
        if tareas_resp.status_code != 200:
            print("Error al obtener tareas:", tareas_resp.text)
            return redirect("lista_procesos_disponibles")

        tareas = tareas_resp.json()
        if not tareas:
            print("No hay tareas disponibles para este caso")
            return redirect("lista_procesos_disponibles")

        task_id = tareas[0]["id"]  # tomamos la primera tarea disponible

        # Completamos la tarea con los datos
        url_completar = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
        resp = session.post(url_completar, headers=headers, json=datos)
        if resp.status_code in [200, 201]:
            print("Instancia avanzada con éxito")
            return redirect("lista_procesos_disponibles")
        else:
            print("Error al avanzar instancia:", resp.text)
            return redirect("lista_procesos_disponibles")

    # GET: mostramos el formulario
    return render(request, "llenar_datos.html")