from django.urls import path
from . import views

urlpatterns = [
    path('proyecto/', views.index, name='proyecto'),
    path('proyecto/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyecto/<int:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyecto/<int:proyecto_id>/etapas/', views.etapas_proyecto, name='etapas_proyecto'),
]
