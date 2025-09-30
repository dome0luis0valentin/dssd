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
            return redirect('lista_users')  # Redirige a otra vista (por ejemplo, lista)
    else:
        form = UserForm()
    return render(request, 'user/alta_user.html', {'form': form})

def bonita_login(request):
    url = f"{url_bonita}/loginservice"
    payload = {
        "username": user,
        "password": password,
        "redirect": "false",
    }

    session = requests.Session()
    response = session.post(url, data=payload)
    print("STATUS:", response.status_code)
    print("COOKIES:", session.cookies.get_dict())
    print("BODY:", response.text)
    if response.status_code == 204:
        request.session["cookies"] = session.cookies.get_dict()
        request.session["headers"] = {
            "X-Bonita-API-Token": session.cookies.get("X-Bonita-API-Token")
        }
        request.session["username_bonita"] = user
        print("Login exitoso")
        return session
    else:
        raise Exception("Error al loguearse en Bonita", response.text)
    
def lista_procesos_disponibles(request):
    procesos = []
    session = bonita_login(request)
    if not session:
        return render(request, 'user/lista_procesos.html', {'procesos': procesos})

    # Obtener token
    cookies = request.session.get("cookies", {})
    headers = request.session.get("headers", {})

    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)

    # Endpoint para procesos que el usuario puede iniciar
    url_user_processes = f"{url_bonita}/API/bpm/process?p=0&c=10"

    try:
        response = session.get(url_user_processes, headers=headers, timeout=10)
        response.raise_for_status()
        procesos = response.json()
        print(f"Cantidad de procesos disponibles: {len(procesos)}")
    except requests.exceptions.RequestException as e:
        print("Error al obtener procesos:", e)
        procesos = []

    return render(request, 'user/lista_procesos.html', {'procesos': procesos})

def iniciar_proceso(request, proceso_id):
    if request.method == "POST":
        proceso_id = request.POST.get("proceso_id", proceso_id)

        # Recuperar token y cookies guardadas en la sesión de Django
        cookies = request.session.get("cookies")
        headers = request.session.get("headers")

        if not cookies or not headers:
            print("No hay sesión activa. Debes loguearte primero.")
            return redirect("login")  # redirige al login

        # Crear sesión de requests para reutilizar cookies
        session = requests.Session()
        session.cookies.update(cookies)

        # URL para iniciar el proceso
        url = f"{url_bonita}/API/bpm/process/{proceso_id}/instantiation"

        resp = session.post(url, headers=headers, json={})
        if resp.status_code in [200, 201]:
            data = resp.json()
            case_id = data.get("caseId")
            print("Proceso iniciado, case_id:", case_id)
            # Guardamos el case_id en la sesión o lo pasamos a la siguiente vista
            request.session["case_id"] = case_id
            request.session["proceso_id"] = proceso_id
            # Redirigimos al formulario para llenar datos
            return redirect("llenar_datos_proceso")
        else:
            print("Error al iniciar proceso:", resp.status_code, resp.text)

        return redirect("lista_procesos_disponibles")
    
def llenar_datos_proceso(request):
    case_id = request.session.get("case_id")
    proceso_id = request.session.get("proceso_id")
    cookies = request.session.get("cookies")
    headers = request.session.get("headers")
    username = request.session.get("username_bonita")

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
