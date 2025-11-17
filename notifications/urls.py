# notifications/urls.py
from django.urls import path
from .views import lista_notificaciones

urlpatterns = [
    path('', lista_notificaciones, name='lista_notificaciones'),
]