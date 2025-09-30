from django.urls import path
from .views import *
urlpatterns = [
    path('', lista_procesos_disponibles, name="lista_procesos_disponibles"),
    path('alta/', alta_user, name='alta_user'),
    path("lista/", lista_users, name="lista_users"),
    path("login/", login_user, name="login_user"),
    path("perfil/", perfil_user, name="perfil_user"),
    path("logout/", logout_user, name="logout_user"),
]