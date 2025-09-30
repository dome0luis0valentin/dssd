from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from user.models import User
from Project.models import Project   # 👈 ajusta el nombre de tu modelo/proyecto real

def home_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")  # si no está logueado, lo manda a login

    # Buscar al usuario actual
    user = User.objects.get(id=user_id)

    # Traer proyectos (ajusta según tu modelo)
    proyectos = Project.objects.all()   # si quieres mostrar todos
    # proyectos = Project.objects.filter(usuario=user)  # si quieres solo los del usuario

    return render(request, "home.html", {
        "user": user,
        "proyectos": proyectos
    })
