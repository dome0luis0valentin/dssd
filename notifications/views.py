# notifications/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def lista_notificaciones(request):
    notificaciones = request.user.notificaciones.order_by('-fecha')
    return render(request, 'notifications/lista.html', {'notificaciones': notificaciones})