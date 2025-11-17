from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notificacion
from Project.models import Proyecto
from Observation.models import Observacion
from CoverageRequest.models import PedidoCobertura
from user.models import User

# 1. Notificar a todos los usuarios cuando se crea un nuevo proyecto
@receiver(post_save, sender=Proyecto)
def notificar_nuevo_proyecto(sender, instance, created, **kwargs):
    if created:
        for usuario in User.objects.all():
            Notificacion.objects.create(
                usuario=usuario,
                mensaje=f"Se ha creado un nuevo proyecto: {instance.nombre}"
            )

# 2. Notificar a todos los usuarios de la ONG originadora cuando se crea una observación
@receiver(post_save, sender=Observacion)
def notificar_observacion(sender, instance, created, **kwargs):
    if created:
        ong = instance.proyecto.originador
        usuarios_ong = User.objects.filter(ong=ong)
        for usuario in usuarios_ong:
            Notificacion.objects.create(
                usuario=usuario,
                mensaje=f"Se ha realizado una observación sobre el proyecto '{instance.proyecto.nombre}'."
            )

# 3. Notificar al usuario que hizo el pedido de cobertura si fue aprobado o rechazado
@receiver(post_save, sender=PedidoCobertura)
def notificar_estado_pedido(sender, instance, **kwargs):
    if instance.estado:
        mensaje = f"Tu pedido de cobertura para el proyecto '{instance.proyecto.nombre}' ha sido aprobado."
    else:
        mensaje = f"Tu pedido de cobertura para el proyecto '{instance.proyecto.nombre}' ha sido rechazado."

    Notificacion.objects.create(
        usuario=instance.usuario,
        mensaje=mensaje
    )

