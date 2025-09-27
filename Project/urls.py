from django.urls import path
from .views import alta_proyecto

urlpatterns = [
    path('alta/<int:case_id>/avanzar/', alta_proyecto, name='alta_proyecto'),
]