from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),       # cambia 'home' a 'index' para que sea consistente
]
