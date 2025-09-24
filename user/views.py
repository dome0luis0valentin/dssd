from django.shortcuts import render, redirect
from .forms import UserForm

def alta_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_users')  # Redirige a otra vista (por ejemplo, lista)
    else:
        form = UserForm()
    return render(request, 'User/altas_users.html', {'form': form})

