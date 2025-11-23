from django.urls import path
from . import views
urlpatterns = [
    path('etapas/cargar/<int:proyecto_id>/', views.cargar_etapas, name='cargar_etapas'),
]