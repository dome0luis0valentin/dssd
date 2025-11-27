from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Compromiso
from .forms import CompromisoForm
from CoverageRequest.models import PedidoCobertura
from user.wraps import session_required
from django.contrib import messages
import urllib.parse
from user.models import User
from Stage.models import Etapa
import requests
from datetime import timedelta
from bonita_utils import url_bonita
from notifications.views import crear_notificacion
from ONG.models import ONG   
from Project.utils import actualizar_estado_proyecto_si_completo  # <-- nueva función

@session_required
def postular_compromiso(request, pedido_id):
    pedido = get_object_or_404(PedidoCobertura, id=pedido_id)
    etapa = pedido.etapas.first()  # una etapa por pedido
    user_id = request.session.get("user_id")
    user = get_object_or_404(User, id=user_id)
    ong_postulante = getattr(user, 'ong', None)

    if request.method == 'POST':
        form = CompromisoForm(request.POST, pedido=pedido)
        if form.is_valid():
            compromiso = form.save(commit=False)
            compromiso.pedido = pedido
            compromiso.responsable = ong_postulante  # ONG que se postula

            # Si es compromiso total, completamos fechas automáticamente
            if compromiso.tipo == 'total' and etapa:
                compromiso.fecha_inicio = etapa.fecha_inicio
                compromiso.fecha_fin = etapa.fecha_fin

            compromiso.save()

            #logica bonita compromiso
            print(f"TRAER TAREA 'Postular Donacion'")

            url_get_task = f"{url_bonita}/API/bpm/humanTask"

            params = {
                'p': 0,   # página
                'c': 20,  # cantidad
                'f': 'displayName=Postular Donacion',
            }

            cookies = request.session.get("cookies")
            headers = request.session.get("headers")

            resp = requests.get(url_get_task, params=params, cookies=cookies, headers=headers, timeout=30)

            print(f"RESPUESTA OBTENER TAREA: {resp.status_code}")
            print(f"RESPUESTA OBTENER TAREA TEXTO: {resp.text}")

            if resp.status_code == 200:
                tasks = resp.json()

                if tasks:
                    tarea = tasks[0]
                    task_id = tarea["id"]
                    print(f"ID de la tarea 'Postular Donacion' encontrada: {task_id}")

                    # Guardar en sesión si querés usarla luego
                    request.session['task_id_postular_donacion'] = task_id
                else:
                    print("⚠️ No se encontró la tarea 'Postular Donacion' (no está lista o no existe).")
            else:
                print(f"❌ Error al obtener tareas: {resp.text}")
                
            descripcion_encoded = urllib.parse.quote(
                f"La ONG {ong_postulante.nombre} se compromete a cubrir el pedido {pedido.id} en las fechas indicadas."
            )
            proyecto_id_actual = request.session.get("proyecto_id_actual")

            url_api_render = (
                f"https://dssd-cloud-bpqf.onrender.com/proyectos/compromisos/"
                f"?descripcion={descripcion_encoded}&proyecto_id={proyecto_id_actual}"
            )

            print(f"🌐 URL FINAL PARA BONITA: {url_api_render}")

                
            payload = {                    
                    # HashMap simple para datos adicionales si es necesario
                    "compromisoInput": {
                        "tipo": compromiso.tipo, 
                        "detalle": compromiso.detalle,
                        "fecha_inicio": str(compromiso.fecha_inicio),
                        "fecha_fin": str(compromiso.fecha_fin),
                        "pedido": int(pedido.id),
                        "responsable": int(ong_postulante.id),
                    },
                    "jwtTokenRender": request.session.get('jwt_token_render'),
                    "descripsion": f"La ONG {ong_postulante.nombre} se compromete a cubrir el pedido {pedido.id} en las fechas indicadas.", 
                    "proyecto_id": request.session.get("proyecto_id_actual"),
                    "url_api_compromiso": str(url_api_render)
            }

            print("\n📦 PAYLOAD FINAL A BONITA:")
            print(payload)
            
           # 2️⃣ Asignar la tarea al usuario actual (obligatorio en Bonita)
            url_assign = f"{url_bonita}/API/bpm/humanTask/{task_id}"

            assign_payload = {
                "assigned_id": request.session.get("bonita_user_id")  # usuario BONITA logueado
            }

            resp_assign = requests.put(
                url_assign,
                json=assign_payload,
                cookies=cookies,
                headers=headers,
                timeout=30
            )

            print(f"ASIGNACIÓN → {resp_assign.status_code} | {resp_assign.text}") 
                        
            # 3️⃣ Si se encontró la tarea → ejecutarla
            if task_id:
                url_execute = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"

                resp_execute = requests.post(
                    url_execute,
                    json=payload,
                    cookies=cookies,
                    headers=headers,
                    timeout=30
                )

                print(f"RESPUESTA EJECUCIÓN TAREA: {resp_execute.status_code}")
                print(f"RESPUESTA TEXT EJECUCIÓN: {resp_execute.text}")

            
            # 🔥 Notificar a todos los usuarios de la ONG propietaria del proyecto
            ong_origen = etapa.proyecto.originador  # ONG propietaria del proyecto
            usuarios_notificar = User.objects.filter(ong=ong_origen)

            for u in usuarios_notificar:
                crear_notificacion(
                    u,
                    f"El Usuario {user.nombre} {user.apellido}, que pertenece a la ONG {ong_postulante.nombre}, "
                    f"postuló a la Etapa '{etapa.nombre}' del Proyecto '{etapa.proyecto.nombre}'.",
                    tipo='info'
                )

            return redirect('etapas_proyecto', proyecto_id=etapa.proyecto.id)

    else:
        form = CompromisoForm(pedido=pedido)

    return render(request, 'postular_compromiso.html', {
        'form': form,
        'pedido': pedido,
        'etapa': etapa
    })


@session_required
def compromisos_etapa(request, etapa_id):
    etapa = get_object_or_404(Etapa, id=etapa_id)
    pedido = etapa.pedido
    compromisos = pedido.compromisos.all()

    calendario = None

    # Crear calendario solo si NO está completado
    if not pedido.estado:
        dias_etapa = (etapa.fecha_fin - etapa.fecha_inicio).days + 1
        calendario = []
        for i in range(dias_etapa):
            dia = etapa.fecha_inicio + timedelta(days=i)
            cubierto = compromisos.filter(
                tipo="parcial", fecha_inicio__lte=dia, fecha_fin__gte=dia
            ).exists()
            calendario.append({"fecha": dia, "cubierto": cubierto})

    return render(request, "lista_compromisos_etapa.html", {
        "etapa": etapa,
        "compromisos": compromisos,
        "pedido": pedido,
        "calendario": calendario,
    })


    
@session_required
def detalle_compromiso(request, compromiso_id):
    compromiso = get_object_or_404(Compromiso, id=compromiso_id)

    return render(request, "detalle_compromiso.html", {
        "compromiso": compromiso,
    })

from django.shortcuts import get_object_or_404, redirect
from .models import Compromiso
from user.models import User
from notifications.views import crear_notificacion
from Project.utils import actualizar_estado_proyecto_si_completo  # <-- nueva función

def aceptar_compromiso(request, id):
    """
    Acepta un compromiso:
    - Si es TOTAL: marca el pedido como completo.
    - Si es PARCIAL: actualiza las fechas cubiertas y si todo está cubierto, marca el pedido como completo.
    - Envía notificaciones a todos los usuarios de la ONG responsable.
    - No elimina el compromiso aceptado.
    - Si todas las etapas del proyecto están completas, cambia el estado del proyecto a 'ejecucion'
      y notifica a todas las ONG responsables de compromisos.
    """
    compromiso = get_object_or_404(Compromiso, id=id)
    pedido = compromiso.pedido
    etapa = pedido.etapas.first()
    proyecto = etapa.proyecto

    # Obtener todos los usuarios de la ONG responsable del compromiso
    usuarios = User.objects.filter(ong=compromiso.responsable)

    # 🔹 Marcar el pedido como completo según el tipo de compromiso
    if compromiso.tipo == 'total':
        pedido.estado = True
        pedido.save()

    elif compromiso.tipo == 'parcial':
        # Pseudocódigo para actualizar fechas parciales
        # actualizar_fechas_cubiertas(compromiso, etapa)
        todas_fechas_cubiertas = True  # reemplazar por lógica real
        if todas_fechas_cubiertas:
            pedido.estado = True
            pedido.save()
            # Comentario: eliminar otros compromisos parciales si hace falta
            # Compromiso.objects.filter(pedido=pedido).exclude(id=compromiso.id).delete()
    
    # 🔹 Si el pedido quedó completo, avanzar tarea en Bonita
    if pedido.estado is True:
        
        cookies = request.session.get("cookies")
        headers = request.session.get("headers")
        bonita_user_id = request.session.get("bonita_user_id")
        case_id = request.session.get('case_id') # asegúrate de tener el case_id de Bonita

        print("Pedido completado → avanzar tarea en Bonita")

        url_get_task = f"{url_bonita}/API/bpm/humanTask"
        params = {
            'p': 0,
            'c': 20,
            'f': 'displayName=Seleccion de candidato',
        }
        
        resp = requests.get(url_get_task, params=params, cookies=cookies, headers=headers, timeout=30)

        if resp.status_code == 200:
            tasks = resp.json()
            if tasks:
                task_id = tasks[0]["id"]
                print(f"ID tarea encontrada: {task_id}")
                
                # 2️⃣ Asignar la tarea al usuario autenticado en Bonita
                url_assign = f"{url_bonita}/API/bpm/userTask/{task_id}"
                data_assign = {"assigned_id": bonita_user_id}
                resp_assign = requests.put(url_assign, json=data_assign, cookies=cookies, headers=headers, timeout=30)

                if resp_assign.status_code in (200, 204):
                    print("🔹 Tarea asignada correctamente → ejecutando")

                    # 3️⃣ Ejecutar la tarea para pasar a "Entrega de donaciones"
                    url_execute = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
                    payload = {
                        "cubierto": True
                    }
                    resp2 = requests.post(url_execute, json=payload ,cookies=cookies, headers=headers, timeout=30)

                    if resp2.status_code == 204:
                        print("🚀 La tarea 'Seleccion de candidato' fue completada en Bonita")
                    else:
                        print(f"⚠️ Error ejecutando tarea: {resp2.text}")
                else:
                    print(f"❌ Error asignando tarea: {resp_assign.text}")
            else:
                print("⚠️ No hay tarea 'Seleccion de candidato' disponible para avanzar")
        else:
            print(f"❌ Error obteniendo tareas: {resp.text}")


    # 🔹 Notificar a los usuarios de la ONG responsable
    for usuario in usuarios:
        crear_notificacion(
            usuario,
            f"Felicidades, usted tiene un compromiso con la etapa '{etapa.nombre}' del proyecto '{proyecto.nombre}'",
            tipo='success'
        )

    # 🔹 Nueva funcionalidad: actualizar estado del proyecto si todas las etapas están completas
    actualizar_estado_proyecto_si_completo(proyecto)

    return redirect(request.META.get("HTTP_REFERER", "/"))



def rechazar_compromiso(request, id):
    """
    Rechaza un compromiso:
    - Envía notificación de agradecimiento a todos los integrantes de la ONG responsable.
    - Elimina el compromiso rechazado.
    """
    compromiso = get_object_or_404(Compromiso, id=id)
    etapa = compromiso.pedido.etapas.first()
    usuarios = User.objects.filter(ong=compromiso.responsable)

    # Notificación de agradecimiento
    for usuario in usuarios:
        crear_notificacion(
            usuario,
            f"Gracias por su participación en la etapa '{etapa.nombre}' del proyecto '{etapa.proyecto.nombre}'",
            tipo='info'
        )

    # Eliminar compromiso rechazado
    compromiso.delete()

    return redirect(request.META.get("HTTP_REFERER", "/"))


@session_required
def entregar_donaciones(request, compromiso_id):
    compromiso = get_object_or_404(Compromiso, id=compromiso_id)

    # 🔹 Marcar como entregado
    compromiso.entregado = True
    compromiso.save()
    
    #logica bonita compromiso
    print(f"TRAER TAREA 'Postular Donacion'")

    url_get_task = f"{url_bonita}/API/bpm/humanTask"

    params = {
    'p': 0,   # página
    'c': 20,  # cantidad
    'f': 'displayName=Entrega de donaciones',
    }

    cookies = request.session.get("cookies")
    headers = request.session.get("headers")
    bonita_user_id = request.session.get("bonita_user_id")

    resp = requests.get(url_get_task, params=params, cookies=cookies, headers=headers, timeout=30)

    print(f"RESPUESTA OBTENER TAREA: {resp.status_code}")
    print(f"RESPUESTA OBTENER TAREA TEXTO: {resp.text}")

    if resp.status_code == 200:
        tasks = resp.json()
        if tasks:
            task_id = tasks[0]["id"]
            print(f"ID tarea encontrada: {task_id}")

            # 1️⃣ Asignar la tarea al usuario actual
            url_assign = f"{url_bonita}/API/bpm/userTask/{task_id}"
            data_assign = {"assigned_id": bonita_user_id}
            resp_assign = requests.put(url_assign, json=data_assign, cookies=cookies, headers=headers, timeout=30)

            if resp_assign.status_code in (200, 204):
                print("🔹 Tarea asignada correctamente → ejecutando")

                # 2️⃣ Ejecutar la tarea
                url_execute = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
                resp_execute = requests.post(url_execute, cookies=cookies, headers=headers, timeout=30)

                if resp_execute.status_code in (200, 204):
                    print("🚀 La tarea 'Entrega de donaciones' fue completada en Bonita")
                    messages.success(request, "Compromiso entregado y tarea 'Entrega de donaciones' completada en Bonita.")
                else:
                    print(f"⚠️ Error ejecutando tarea: {resp_execute.text}")
                    messages.warning(request, "Compromiso entregado, pero error ejecutando la tarea en Bonita.")
            else:
                print(f"❌ Error asignando tarea: {resp_assign.text}")
                messages.warning(request, "Compromiso entregado, pero error asignando la tarea en Bonita.")
        else:
            print("⚠️ No hay tarea 'Entrega de donaciones' disponible para avanzar")
            messages.warning(request, "Compromiso entregado, pero no se encontró tarea 'Entrega de donaciones' en Bonita.")
    else:
        print(f"❌ Error obteniendo tareas: {resp.text}")
        messages.error(request, "Compromiso entregado, pero fallo la conexión con Bonita.")

    # 🔹 Volver a la página anterior
    return redirect(request.META.get("HTTP_REFERER", "/"))