from django.db import models
from BoardOfDirectors.models import ConsejoDirectivo

class User(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    email = models.EmailField(unique=True)
    
        # Un usuario pertenece a un único consejo directivo
    consejo = models.ForeignKey(
        ConsejoDirectivo,
        on_delete=models.CASCADE,
        related_name='miembros',
        null=True, blank=True  # opcional, si hay usuarios que no son parte de un consejo
    )


    def __str__(self):
        return f"{self.nombre} {self.apellido}"
