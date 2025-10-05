from django.db import models

class ONG(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Participa(models.Model):
    ong = models.ForeignKey("ONG.ONG", on_delete=models.CASCADE)
    proyecto = models.ForeignKey("Project.Proyecto", on_delete=models.CASCADE)
    fecha_inicio = models.DateField(auto_now_add=True)  # info extra

    def __str__(self):
        return f"{self.ong.nombre} participa en {self.proyecto.nombre}"