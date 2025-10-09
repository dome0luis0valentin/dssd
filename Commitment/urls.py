from django.urls import path
from . import views

urlpatterns = [
    path('postular/<int:pedido_id>/', views.postular_compromiso, name='postular_compromiso'),
]
