from django.shortcuts import render, get_object_or_404, redirect
from .models import Compromiso
from .forms import CompromisoForm
from CoverageRequest.models import PedidoCobertura
from user.wraps import session_required
from user.models import User

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