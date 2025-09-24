from django.db import models
from Project.models import Proyecto
from user.models import User as Usuario

class ONG(models.Model):
    nombre = models.CharField(max_length=255)
    # Relación Many-to-Many: una ONG puede tener múltiples usuarios y un usuario puede pertenecer a múltiples ONGs
    usuarios = models.ManyToManyField(Usuario, related_name='ongs', blank=True)

    def __str__(self):
        return self.nombre

class Participa(models.Model):
    ong = models.ForeignKey(ONG, on_delete=models.CASCADE)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    fecha_inicio = models.DateField(auto_now_add=True)  # información extra

    def __str__(self):
        return f"{self.ong.nombre} participa en {self.proyecto.nombre}"