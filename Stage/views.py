from django.shortcuts import render, redirect, get_object_or_404
from .models import Etapa
from .forms import EtapaForm
from Project.models import Proyecto

def cargar_etapas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == "POST":
        form = EtapaForm(request.POST)
        if form.is_valid():
            form.save(proyecto=proyecto.id)

            # Diferenciamos según el botón presionado
            if request.POST.get("action") == "agregar":
                # Redirigir a la misma página para agregar otra etapa
                return redirect('cargar_etapas', proyecto_id=proyecto.id)
            elif request.POST.get("action") == "guardar":
                # Redirigir a la vista de detalle del proyecto (futura)
                return redirect('detalle_proyecto', pk=proyecto.id)
    else:
        form = EtapaForm()

    return render(request, 'cargar_etapa.html', {
        'form': form,
        'proyecto': proyecto,
    })

