from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .forms import UserForm
from django.contrib import messages
from user.models import User

def alta_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_users')
    else:
        form = UserForm()
    return render(request, 'user/alta_user.html', {'form': form})

@login_required
def lista_users(request):
    usuarios = User.objects.all()
    return render(request, 'user/lista_users.html', {"usuarios": usuarios})

def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")   # 👈 corregido
        password = request.POST.get("password")
        
        print("DEBUG email:", email)
        print("DEBUG password:", password)
        
        try:
            user = User.objects.get(email=email)
            
            if password == user.password:   # 👈 con texto plano funciona
                request.session['user_id'] = user.id
                request.session['user_name'] = user.nombre
                return redirect("index")
            else:
                messages.error(request, "Usuario o Contraseña incorrecta")
        except User.DoesNotExist:
            messages.error(request, "Usuario o Contraseña incorrecta")

    return render(request, "login.html")

@login_required
def perfil_user(request):
    return render(request, "perfil.html", {"usuario": request.user})

@login_required
def logout_user(request):
    logout(request)
    return redirect("login_user")
