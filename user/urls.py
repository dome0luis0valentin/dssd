from django.urls import path
from .views import *

urlpatterns = [
    path('', lista_procesos_disponibles, name="lista_procesos_disponibles"),
    path('login/', login_view , name='login'), #login
    path('logout/', logout_view, name='logout'),
    #path('alta/', alta_user, name='alta_user'), #altas de usuarios
    path('perfil/', perfil, name='perfil'), # Ver perfil
    path('procesos/', lista_procesos_disponibles, name="lista_procesos_disponibles"),
    path('procesos/iniciar/<int:proceso_id>/', iniciar_proceso, name='iniciar_proceso'),
    path('procesos/llenar_datos/', llenar_datos_proceso, name='llenar_datos_proceso')
]