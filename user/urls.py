from django.urls import path
from .views import alta_user

urlpatterns = [
    path('alta/', alta_user, name='alta_user'),
]