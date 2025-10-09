from django.shortcuts import render

# Create your views here.
# compromiso/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Compromiso
from .forms import CompromisoForm
from CoverageRequest.models import PedidoCobertura

def postular_compromiso(request, pedido_id):
    pedido = get_object_or_404(PedidoCobertura, id=pedido_id)

    if request.method == 'POST':
        form = CompromisoForm(request.POST, pedido=pedido)
        if form.is_valid():
            compromiso = form.save(commit=False)
            compromiso.pedido = pedido

            # Si el tipo es 'total', setear fechas igual al pedido
            if compromiso.tipo == 'total':
                # Asumiendo que el pedido tiene fecha_inicio y fecha_fin vía Etapa
                if pedido.etapas.exists():
                    etapa = pedido.etapas.first()  # tomo la primera etapa del pedido
                    compromiso.fecha_inicio = etapa.fecha_inicio
                    compromiso.fecha_fin = etapa.fecha_fin
            # Si es parcial, usa lo que el usuario seleccionó
            compromiso.save()
            return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        form = CompromisoForm(pedido=pedido)

    return render(request, 'postular_compromiso.html', {
        'form': form,
        'pedido': pedido,
    })
