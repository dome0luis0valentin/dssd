from django.urls import path
from . import views

app_name = "bonita"

urlpatterns = [
    path("procesos/", views.lista_procesos_disponibles, name="lista_procesos"),
    path("proceso/<str:proceso_id>/iniciar/", views.iniciar_proceso, name="iniciar_proceso"),
    path("proceso/llenar/", views.llenar_datos_proceso, name="llenar_datos_proceso"),
]
