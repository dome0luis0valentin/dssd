from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.bonita_login, name="bonita_login"),
    path("procesos/", views.lista_procesos_disponibles, name="lista_procesos_disponibles"),
    path("iniciar/<str:proceso_id>/", views.iniciar_proceso, name="iniciar_proceso"),
    path("llenar/", views.llenar_datos_proceso, name="llenar_datos_proceso"),
]
