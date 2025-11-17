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
    # Interface Gerencial para Observaciones
    path('interface-gerencial/', views.interface_gerencial, name='interface_gerencial'),
    path('gerencial/proyecto/<int:proyecto_id>/', views.detalle_proyecto_gerencial, name='detalle_proyecto_gerencial'),
    path('gerencial/proyecto/<int:proyecto_id>/observacion/', views.crear_observacion, name='crear_observacion'),
    path('gerencial/proyecto/<int:proyecto_id>/etapa/<int:etapa_id>/observacion/', views.crear_observacion, name='crear_observacion_etapa'),
    # Marcar observación como resuelta
    path('observacion/<int:observacion_id>/resolver/', views.marcar_observacion_resuelta, name='marcar_observacion_resuelta'),
]