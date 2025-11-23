from django.urls import path
from . import views

urlpatterns = [
    path('postular/<int:pedido_id>/', views.postular_compromiso, name='postular_compromiso'),
    path('etapa/<int:etapa_id>/compromisos/', views.compromisos_etapa, name='compromisos_etapa'),
    path('compromiso/<int:compromiso_id>/', views.detalle_compromiso, name='detalle_compromiso'),
    path('compromisos/<int:id>/aceptar/', views.aceptar_compromiso, name='aceptar_compromiso'),
    path('compromisos/<int:id>/rechazar/', views.rechazar_compromiso, name='rechazar_compromiso'),

]
