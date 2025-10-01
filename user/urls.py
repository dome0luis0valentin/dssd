from django.urls import path
from .views import alta_user,lista_procesos_disponibles, iniciar_proceso, llenar_datos_proceso

urlpatterns = [
    path('', lista_procesos_disponibles, name="lista_procesos_disponibles"),
    path('alta/', alta_user, name='alta_user'), #login
    path('procesos/', lista_procesos_disponibles, name="lista_procesos_disponibles"),
    path('procesos/iniciar/<int:proceso_id>/', iniciar_proceso, name='iniciar_proceso'),
    path('procesos/llenar_datos/', llenar_datos_proceso, name='llenar_datos_proceso')
]