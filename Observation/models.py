from django.db import models
from Project.models import Proyecto  
from BoardOfDirectors.models import ConsejoDirectivo

class Observacion(models.Model):
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

    def __str__(self):
        return f"Observación para {self.proyecto.nombre}: {self.descripcion[:30]}..."
