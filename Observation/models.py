from django.db import models
from Project.models import Proyecto  
from BoardOfDirectors.models import ConsejoDirectivo

class Observacion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('resuelta', 'Resuelta'),
    ]
    
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='observaciones'
    )
    
    consejo = models.ForeignKey(
        ConsejoDirectivo,
        on_delete=models.CASCADE,
        related_name='observaciones'
    )
    
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Observación para {self.proyecto.nombre}: {self.descripcion[:30]}..."
    
    def marcar_como_resuelta(self):
        """Marca la observación como resuelta"""
        from django.utils import timezone
        self.estado = 'resuelta'
        self.fecha_resolucion = timezone.now()
        self.save()
