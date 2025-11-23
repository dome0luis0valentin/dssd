from django.db import models
from ONG.models import ONG

class Proyecto(models.Model):
    # Opciones para el estado
    ESTADO_CHOICES = [
        ('proceso', 'En proceso'),
        ('ejecucion', 'En ejecución'),
        ('finalizado', 'Finalizado'),
    ]

    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='proceso')
    
    # Relación One-to-Many: un proyecto tiene un originador
    originador = models.ForeignKey(ONG, on_delete=models.CASCADE, related_name='proyectos_originados')

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

