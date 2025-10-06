from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.core.paginator import Paginator
from .models import Proyecto
from Stage.models import Etapa
from user.models import User
from CoverageRequest.models import PedidoCobertura
from .forms import ProyectoForm, EtapaForm

import requests
url_bonita = "http://localhost:8080/bonita"

def index(request):
    proyectos = []
    session_cookies = request.session.get("cookies")

    if not session_cookies:
        return render(request, "proyecto_index.html", {"proyectos": proyectos})

    # Obtener cookies y headers guardados en la sesión
    cookies = request.session.get("cookies", {})
    headers = request.session.get("headers", {})

    # Crear sesión de requests
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)

    # Endpoint para proyectos (ejemplo: podrías usar otra API en Bonita)
    url_proyectos = f"{url_bonita}/API/bpm/process?p=0&c=50"

    try:
        response = session.get(url_proyectos, headers=headers, timeout=10)
        response.raise_for_status()
        proyectos = response.json()
        print(f"Cantidad de proyectos disponibles: {len(proyectos)}")
    except requests.exceptions.RequestException as e:
        print("Error al obtener proyectos:", e)
        proyectos = []

    # Paginación con Django
    paginator = Paginator(proyectos, 5)  # 5 proyectos por página
    page_number = request.GET.get("page")
    proyectos_page = paginator.get_page(page_number)

    return render(request, "proyecto_index.html", {"proyectos": proyectos_page})

def crear_proyecto(request):
    if request.method == "POST":
        proyecto_form = ProyectoForm(request.POST)
        if proyecto_form.is_valid():
            # Recuperamos el user_id desde la sesión
            user_id = request.session.get("user_id")
            user = User.objects.get(id=user_id)

            # Creamos el proyecto pero no lo guardamos aún
            proyecto = proyecto_form.save(commit=False)
            proyecto.originador = user.ong  # ONG del usuario logueado
            proyecto.estado = "Proceso"      # Estado por defecto
            proyecto.save()  # Guardamos el proyecto

            # Redirigimos a la vista de carga de etapas (en otra app)
            return redirect("cargar_etapas", proyecto_id=proyecto.id)
    else:
        proyecto_form = ProyectoForm()

    return render(request, "proyecto_crear.html", {
        "proyecto_form": proyecto_form,
    })

def iniciar_proceso_bonita(proyecto):
    url = "http://localhost:8080/bonita/API/bpm/process/PROJECT_ID/instantiation"
    data = {
        "nombreProyecto": proyecto.nombre,
        "descripcion": proyecto.descripcion,
        "estado": proyecto.estado,
    }
    response = requests.post(url, json=data, auth=("admin", "admin"))
    return response.json()

def notificar_etapa_bonita(etapa):
    url = f"http://localhost:8080/bonita/API/bpm/caseVariable/{etapa.proyecto.id}"
    data = {
        "etapaNombre": etapa.nombre,
        "fechaInicio": str(etapa.fecha_inicio),
        "fechaFin": str(etapa.fecha_fin) if etapa.fecha_fin else "",
        "tipoCobertura": etapa.pedido.tipo_cobertura.nombre
    }
    response = requests.put(url, json=data, auth=("admin", "admin"))
    return response.json()

def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    return render(request, "proyecto_detalle.html", {
        "proyecto": proyecto,
        "etapas": proyecto.etapas.all()
    })

"""
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
"""