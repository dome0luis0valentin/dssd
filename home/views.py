from django.shortcuts import render, redirect
from user.models import User
from Project.models import Proyecto # Ajusta el nombre de la app si es distinto

def home_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = User.objects.get(id=user_id)

    # Filtrar proyectos por estado
    proyectos_proceso = Proyecto.objects.filter(estado="En Proceso")
    proyectos_ejecucion = Proyecto.objects.filter(estado="En Ejecución")
    proyectos_finalizados = Proyecto.objects.filter(estado="Finalizado")

    return render(request, "home.html", {
        "usuario": user,
        "proyectos_proceso": proyectos_proceso,
        "proyectos_ejecucion": proyectos_ejecucion,
        "proyectos_finalizados": proyectos_finalizados,
    })
