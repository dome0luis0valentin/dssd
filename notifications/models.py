from django.db import models
from user.models import User

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('success', 'Éxito'),
        ('danger', 'Urgente'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True, null=True, help_text="URL de destino opcional")
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.usuario.nombre} - {self.mensaje[:50]}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.save()
