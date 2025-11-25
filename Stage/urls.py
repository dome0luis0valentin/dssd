from django.urls import path
from . import views
urlpatterns = [
    path('etapas/cargar/<int:proyecto_id>/', views.cargar_etapas, name='cargar_etapas'),
    path('bonita/consultar/', views.consultar_datos_bonita, name='consultar_datos_bonita'),
    path('bonita/procesos/', views.obtener_todos_los_procesos_bonita, name='obtener_procesos_bonita'),
    path('bonita/ejecutar-tarea/', views.ejecutar_tarea_manual, name='ejecutar_tarea_manual'),
    path('bonita/verificar-tarea/', views.verificar_tarea_ejecutada, name='verificar_tarea_ejecutada'),
]