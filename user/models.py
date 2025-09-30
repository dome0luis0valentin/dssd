from django.db import models
from BoardOfDirectors.models import ConsejoDirectivo
from django.contrib.auth.hashers import make_password

class User(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # almacenar password encriptada
    
    consejo = models.ForeignKey(
        ConsejoDirectivo,
        on_delete=models.CASCADE,
        related_name='miembros',
        null=True,
        blank=True
    )

    def set_password(self, raw_password):
        """Encriptar y guardar la contraseña"""
        self.password = make_password(raw_password)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
