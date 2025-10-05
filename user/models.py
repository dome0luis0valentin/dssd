from django.db import models
from ONG.models import ONG
from BoardOfDirectors.models import ConsejoDirectivo
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    email = models.EmailField(unique=True)  # será usado como username
    password = models.CharField(max_length=128)  # para guardar contraseña hasheada
    
        # Un usuario pertenece a una única ONG
    ong = models.ForeignKey(ONG, on_delete=models.CASCADE, null=True, blank=True)

    
    # Un usuario pertenece a un único consejo directivo
    consejo = models.ForeignKey(
        ConsejoDirectivo,
        on_delete=models.CASCADE,
        related_name='miembros',
        null=True, blank=True
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    # Método para establecer contraseña hasheada
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()
    
    # Método para verificar contraseña
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
