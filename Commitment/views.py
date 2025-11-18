from django.shortcuts import render, get_object_or_404, redirect
from .models import Compromiso
from .forms import CompromisoForm
from CoverageRequest.models import PedidoCobertura
from user.wraps import session_required
from user.models import User
from Stage.models import Etapa
from datetime import timedelta
from notifications.views import crear_notificacion
from ONG.models import ONG   

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
    compromisos = etapa.pedido.compromisos.all()

    calendario = None

    # Crear calendario solo si NO hay compromisos totales
    if not compromisos.filter(tipo="total").exists():
        dias_etapa = (etapa.fecha_fin - etapa.fecha_inicio).days + 1
        calendario = []
        for i in range(dias_etapa):
            dia = etapa.fecha_inicio + timedelta(days=i)
            cubierto = compromisos.filter(tipo="parcial", fecha_inicio__lte=dia, fecha_fin__gte=dia).exists()
            calendario.append({"fecha": dia, "cubierto": cubierto})

    return render(request, "lista_compromisos_etapa.html", {
        "etapa": etapa,
        "compromisos": compromisos,
        "pedido": etapa.pedido,
        "calendario": calendario,
    })

    
@session_required
def detalle_compromiso(request, compromiso_id):
    compromiso = get_object_or_404(Compromiso, id=compromiso_id)

    return render(request, "detalle_compromiso.html", {
        "compromiso": compromiso,
    })

def aceptar_compromiso(request, id):
    """
    Acepta un compromiso:
    - Si es TOTAL: marca el pedido como completo.
    - Si es PARCIAL: actualiza las fechas cubiertas y si todo está cubierto, marca el pedido como completo.
    - Envía notificaciones a todos los usuarios de la ONG responsable.
    - No elimina el compromiso aceptado.
    """
    compromiso = get_object_or_404(Compromiso, id=id)
    pedido = compromiso.pedido
    etapa = pedido.etapas.first()
    
    # Obtener todos los usuarios de la ONG responsable
    usuarios = User.objects.filter(ong=compromiso.responsable)

    if compromiso.tipo == 'total':
        pedido.estado = True
        pedido.save()

        # Notificar a todos los integrantes de la ONG responsable
        for usuario in usuarios:
            crear_notificacion(
                usuario,
                f"Felicidades, usted tiene un compromiso con la etapa '{etapa.nombre}' del proyecto '{etapa.proyecto.nombre}'",
                tipo='success'
            )
        # Comentario: aquí se pueden eliminar compromisos pendientes de esta etapa
        # y enviar otras notificaciones si hace falta

    elif compromiso.tipo == 'parcial':
        # Pseudocódigo para actualizar fechas parciales
        # actualizar_fechas_cubiertas(compromiso, etapa)
        
        todas_fechas_cubiertas = True  # reemplazar por lógica real
        if todas_fechas_cubiertas:
            pedido.estado = True
            pedido.save()
            # Comentario: eliminar otros compromisos parciales y enviar notificaciones a los afectados
            # Compromiso.objects.filter(pedido=pedido).exclude(id=compromiso.id).delete()
            # enviar_notificacion_usuarios(etapa)

        for usuario in usuarios:
            crear_notificacion(
                usuario,
                f"Felicidades, usted tiene un compromiso con la etapa '{etapa.nombre}' del proyecto '{etapa.proyecto.nombre}'",
                tipo='success'
            )

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
