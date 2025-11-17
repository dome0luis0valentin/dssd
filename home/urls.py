from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('colaboraciones/', views.mis_colaboraciones, name='mis_colaboraciones'),
    path('compromisos/', views.mis_compromisos, name='mis_compromisos'),
    path('observaciones/', views.observaciones, name='observaciones'),
    path('dashboard-gerencial/', views.dashboard_gerencial, name='dashboard_gerencial'),
    path('reportes/', views.reportes, name='reportes'),
    path('panel-seguimiento/', views.panel_seguimiento, name='panel_seguimiento'),
    path('proyecto/<int:proyecto_id>/seguimiento/', views.detalle_proyecto_seguimiento, name='detalle_proyecto_seguimiento'),
]