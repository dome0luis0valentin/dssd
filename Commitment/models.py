from django.db import models
from CoverageRequest.models import PedidoCobertura
from ONG.models import ONG

class Compromiso(models.Model):
    # Opciones para el tipo de compromiso
    TIPO_CHOICES = [
        ('total', 'Total'),
        ('parcial', 'Parcial'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    detalle = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)  # opcional si aún no termina
    
    # Relación One-to-Many: un compromiso pertenece a un pedido de cobertura
    pedido = models.ForeignKey(PedidoCobertura, on_delete=models.CASCADE, related_name='compromisos')

    # Relación One-to-Many: un compromiso tiene una ONG responsable
    responsable = models.ForeignKey(ONG, on_delete=models.CASCADE, related_name='compromisos_responsables')
    def __str__(self):
        return f"{self.tipo.capitalize()} - {self.detalle[:30]}..."

