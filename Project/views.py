import base64
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.core.paginator import Paginator
from .models import Proyecto
from Stage.models import Etapa
from user.models import User
from CoverageRequest.models import PedidoCobertura
from .forms import ProyectoForm
from user.wraps import session_required
import requests

url_bonita = "http://localhost:8080/bonita"

def index(request):
    # 🔹 1️⃣ Guardar las IDs de procesos en sesión (para usarlas luego en crear_proyecto)
    cookies = request.session.get("cookies", {})
    headers = request.session.get("headers", {})
    
    if cookies and headers:
        session = requests.Session()
        for name, value in cookies.items():
            session.cookies.set(name, value)

        try:
            # Ciclo de Vida
            resp_ciclo = session.get(f"{url_bonita}/API/bpm/process", 
                                     params={"f": "name=Ciclo de Vida de Proyecto"},
                                     headers=headers, timeout=10)
            if resp_ciclo.status_code == 200 and resp_ciclo.json():
                request.session["process_id_ciclo_vida"] = resp_ciclo.json()[0]["id"]
                print(f"✅ Ciclo de Vida de Proyecto -> ID: {resp_ciclo.json()[0]['id']}")

            # Ciclo de Observaciones
            resp_obs = session.get(f"{url_bonita}/API/bpm/process", 
                                   params={"f": "name=Ciclo de Observaciones"},
                                   headers=headers, timeout=10)
            if resp_obs.status_code == 200 and resp_obs.json():
                request.session["process_id_ciclo_observacion"] = resp_obs.json()[0]["id"]
                print(f"✅ Ciclo de Observaciones -> ID: {resp_obs.json()[0]['id']}")
        except Exception as e:
            print("⚠️ Error al obtener IDs de procesos:", e)

    # 🔹 2️⃣ Obtener proyectos desde tu base de datos local
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    user_ong = user.ong
    proyectos = Proyecto.objects.exclude(originador=user_ong ).order_by("-id")

    # 🔹 3️⃣ Paginación
    paginator = Paginator(proyectos, 5)
    page_number = request.GET.get("page")
    proyectos_page = paginator.get_page(page_number)

    return render(request, "proyecto_index.html", {
        "proyectos": proyectos_page
    })


def crear_proyecto(request):
    if request.method == "POST":
        proyecto_form = ProyectoForm(request.POST)
        if proyecto_form.is_valid():
            user_id = request.session.get("user_id")
            user = User.objects.get(id=user_id)

            proyecto = proyecto_form.save(commit=False)
            print("📝 Creando proyecto:", proyecto.nombre, " user ", user.ong, user)
            proyecto.originador = user.ong
            proyecto.estado = "Proceso"
            proyecto.save()
            
            return redirect("cargar_etapas", proyecto_id=proyecto.id)

    else:
        proyecto_form = ProyectoForm()

    return render(request, "proyecto_crear.html", {"proyecto_form": proyecto_form})

@session_required
def etapas_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    request.session["proyecto_id_actual"] = proyecto.id

    # 🔹 Traer SOLO las etapas cuyo pedido de cobertura NO esté completo
    etapas = (
        Etapa.objects
        .filter(proyecto=proyecto, pedido__estado=False)
        .select_related('pedido', 'pedido__tipo_cobertura')
    )

    return render(request, 'listado_etapas.html', {
        'proyecto': proyecto,
        'etapas': etapas,
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
def finalizar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, id=pk)

    proyecto.estado = "finalizado"
    proyecto.save()
    
     #logica bonita compromiso
    print(f"TRAER TAREA 'Comienzo ejecucion'")
    url_bonita = "http://localhost:8080/bonita"
    cookies = request.session.get("cookies")
    headers = request.session.get("headers")
    bonita_user_id = request.session.get("bonita_user_id")

    url_get_task = f"{url_bonita}/API/bpm/humanTask"

    params = {
        'p': 0,   # página
        'c': 20,  # cantidad
        'f': 'displayName=Comienzo ejecucion',
    }

    resp = requests.get(url_get_task, params=params, cookies=cookies, headers=headers, timeout=30)

    print(f"RESPUESTA OBTENER TAREA: {resp.status_code}")
    print(f"RESPUESTA OBTENER TAREA TEXTO: {resp.text}")
    
    if resp.status_code == 200:
            tasks = resp.json()
            if tasks:
                task_id = tasks[0]["id"]
                print(f"📌 ID de tarea encontrada en Bonita: {task_id}")

                # 2️⃣ Asignar tarea al usuario
                url_assign = f"{url_bonita}/API/bpm/userTask/{task_id}"
                data_assign = {"assigned_id": bonita_user_id}

                resp_assign = requests.put(url_assign, json=data_assign, cookies=cookies, headers=headers, timeout=30)
                print(f"🔁 Respuesta asignar: {resp_assign.status_code} → {resp_assign.text}")

                if resp_assign.status_code in (200, 204):
                    # 3️⃣ Ejecutar tarea
                    url_execute = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
                    payload = {"fin": True}  # variable que espera tu proceso — cámbiala si es otra

                    resp_exec = requests.post(url_execute, json=payload, cookies=cookies, headers=headers, timeout=30)
                    print(f"🚀 Respuesta ejecutar tarea: {resp_exec.status_code} → {resp_exec.text}")

                    if resp_exec.status_code in (200, 204):
                        messages.success(request,
                            "Proyecto finalizado y proceso de Bonita avanzado correctamente."
                        )
                    else:
                        messages.warning(request,
                            "Proyecto finalizado, pero ocurrió un error al ejecutar la tarea en Bonita."
                        )
                else:
                    messages.warning(request,
                        "Proyecto finalizado, pero no se pudo asignar la tarea en Bonita."
                    )
            else:
                print("⚠️ No hay tarea 'Comienzo ejecucion' disponible actualmente")
                messages.warning(request,
                    "Proyecto finalizado pero no hay tarea activa en Bonita para avanzar."
                )
    else:
            messages.warning(request,
                "Proyecto finalizado pero Bonita devolvió un error al obtener tareas."
            )

    return redirect('detalle_proyecto_seguimiento', pk)