from .models import Proyecto
from notifications.views import crear_notificacion

def actualizar_estado_proyecto_si_completo(proyecto):
    """
    Cambia el estado del proyecto a 'ejecucion' si todas sus etapas
    tienen pedidos de cobertura completos.
    Notifica a todos los usuarios de las ONG responsables de compromisos.
    """
    etapas_incompletas = proyecto.etapas.filter(pedido__estado=False)
    
    if not etapas_incompletas.exists():
        if proyecto.estado != 'ejecucion':
            proyecto.estado = 'ejecucion'
            proyecto.save()
            
            # Notificar a todas las ONG con compromisos en este proyecto
            ogns = set()
            for etapa in proyecto.etapas.all():
                for compromiso in etapa.pedido.compromisos.all():
                    ogns.add(compromiso.responsable)
            
            for ong in ogns:
                for usuario in ong.user_set.all():  # suponiendo relación ONG -> Usuarios
                    crear_notificacion(
                        usuario,
                        f"El Proyecto '{proyecto.nombre}' ha empezado",
                        tipo='info'
                    )
