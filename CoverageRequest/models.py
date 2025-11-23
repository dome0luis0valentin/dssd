from django.db import models
from TypeCoverage.models import TipoCobertura  

class PedidoCobertura(models.Model):
    estado = models.BooleanField(default=False)  # False = pendiente, True = completo
    tipo_cobertura = models.ForeignKey(TipoCobertura, on_delete=models.CASCADE, related_name='pedidos')

    def __str__(self):
        estado_str = "Aprobado" if self.estado else "Pendiente"
        return f"{self.tipo_cobertura.nombre} - {estado_str}"
