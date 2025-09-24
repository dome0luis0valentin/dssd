from django.db import models
from CoverageRequest.models import PedidoCobertura
from Project.models import Proyecto  

class Etapa(models.Model):
    
    # Relación One-to-Many: un Etapa tiene un proyecto
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='etapas')
    
    pedido = models.ForeignKey(PedidoCobertura, on_delete=models.CASCADE, related_name='etapas')
    nombre = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)  # opcional si la etapa no terminó todavía

    def __str__(self):
        return f"{self.nombre} ({self.pedido.tipo_cobertura.nombre})"

