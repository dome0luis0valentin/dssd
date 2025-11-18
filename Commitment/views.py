from django.shortcuts import render, get_object_or_404, redirect
from .models import Compromiso
from .forms import CompromisoForm
from CoverageRequest.models import PedidoCobertura
from user.wraps import session_required
from user.models import User
from Stage.models import Etapa
from datetime import timedelta

@session_required
def postular_compromiso(request, pedido_id):
    pedido = get_object_or_404(PedidoCobertura, id=pedido_id)
    etapa = pedido.etapas.first()  # suponiendo que cada etapa tiene un solo pedido
    # Recuperamos el usuario logueado desde la sesión
    user_id = request.session.get("user_id")
    user = get_object_or_404(User, id=user_id)
    ong = getattr(user, 'ong', None)  # ONG asociada al usuario

    if request.method == 'POST':
        form = CompromisoForm(request.POST, pedido=pedido)
        if form.is_valid():
            compromiso = form.save(commit=False)
            compromiso.pedido = pedido
            compromiso.responsable = ong  # asignación automática
            if compromiso.tipo == 'total' and etapa:
                compromiso.fecha_inicio = etapa.fecha_inicio
                compromiso.fecha_fin = etapa.fecha_fin
            compromiso.save()
            return redirect('etapas_proyecto', proyecto_id=etapa.proyecto.id)
    else:
        form = CompromisoForm(pedido=pedido)

    return render(request, 'postular_compromiso.html', {'form': form, 'pedido': pedido, 'etapa': etapa})


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
    Lógica para aceptar un compromiso
    """
    compromiso = get_object_or_404(Compromiso, id=id)
    pedido = compromiso.pedido
    etapa = pedido.etapas.first()  # suponemos que cada pedido pertenece a una etapa
    
    # Si el compromiso es TOTAL
    if compromiso.tipo == 'total':
        # Marcamos el pedido como completo
        pedido.estado = True
        pedido.save()
        
        # Comentario: Aquí se puede eliminar los demás compromisos pendientes de esta etapa
        # y enviar notificación a los usuarios afectados
        # Ejemplo:
        # Compromiso.objects.filter(pedido=pedido).exclude(id=compromiso.id).delete()
        # enviar_notificacion_usuarios(etapa)
    
    # Si el compromiso es PARCIAL
    elif compromiso.tipo == 'parcial':
        # Actualizar las fechas cubiertas en la etapa
        # Suponemos que tenemos un campo calendario o lista de fechas pendientes
        # Comentario: aquí iría la lógica para marcar las fechas del compromiso como "cubiertas"
        # ejemplo pseudocódigo:
        # for fecha in compromiso.fecha_inicio ... compromiso.fecha_fin:
        #     marcar_fecha_cubierta(fecha, etapa)
        
        # Verificamos si todas las fechas de la etapa están cubiertas
        # Si todas las fechas se cubrieron, marcar el pedido como completo
        todas_fechas_cubiertas = True  # reemplazar con verificación real
        if todas_fechas_cubiertas:
            pedido.estado = True
            pedido.save()
            
            # Comentario: eliminar compromisos parciales pendientes y enviar notificación
            # Compromiso.objects.filter(pedido=pedido).exclude(id=compromiso.id).delete()
            # enviar_notificacion_usuarios(etapa)
    
    # Guardar el estado del compromiso aceptado (opcional)
    compromiso.estado = 'Aceptado'
    compromiso.save()
    
    return redirect(request.META.get("HTTP_REFERER", "/"))

def rechazar_compromiso(request, id):
    """
    Lógica para rechazar un compromiso.
    Por ahora solo redirige y se deja la misma lógica para eliminar y notificar en el futuro.
    """
    compromiso = get_object_or_404(Compromiso, id=id)
    
    # Comentario: Aquí se puede eliminar el compromiso y notificar a los usuarios
    # ejemplo:
    # compromiso.delete()
    # enviar_notificacion_usuarios(etapa)
    
    return redirect(request.META.get("HTTP_REFERER", "/"))
