# notifications/views.py
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from Project.models import Proyecto
from notifications.models import Notificacion
from user.models import User

@login_required
def lista_notificaciones(request):
    notificaciones = request.user.notificaciones.order_by('-fecha')
    return render(request, 'notifications/lista.html', {'notificaciones': notificaciones})


def finalizar_etapas(request, proyecto_id):
    proyecto = Proyecto.objects.get(id=proyecto_id)

    # Marcar el proyecto como listo (opcional)
    proyecto.estado = "Listo"
    proyecto.save()

    # Notificar a todos los usuarios
    usuarios = User.objects.exclude(id=request.session.get("user_id"))  # excluye al originador si querés
    for usuario in usuarios:
        Notificacion.objects.create(
            usuario=usuario,
            mensaje=f"Se ha creado un nuevo proyecto: '{proyecto.nombre}'",
            leida=False,
            url=f"/proyecto/detalle/{proyecto.id}/"
        )

    print("✅ Notificación enviada a todos los usuarios")
    return redirect("proyecto_lista")  # o cualquier vista general que uses