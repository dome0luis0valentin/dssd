from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='index'),       # cambia 'home' a 'index' para que sea consistente
]
