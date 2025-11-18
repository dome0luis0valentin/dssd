# notifications/views.py
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from Project.models import Proyecto
from notifications.models import Notificacion
from user.models import User
from user.wraps import session_required
from user.utils import get_user_context

@session_required
def lista_notificaciones(request):
    """Vista para mostrar todas las notificaciones del usuario"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    
    # Obtener todas las notificaciones del usuario
    notificaciones = usuario.notificaciones.all()
    
    # Estadísticas
    total_notificaciones = notificaciones.count()
    no_leidas = notificaciones.filter(leida=False).count()
    leidas = notificaciones.filter(leida=True).count()
    
    # Separar por estado
    notificaciones_no_leidas = notificaciones.filter(leida=False)
    notificaciones_leidas = notificaciones.filter(leida=True)
    
    context = user_context.copy()
    context.update({
        'notificaciones': notificaciones,
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'notificaciones_leidas': notificaciones_leidas,
        'estadisticas': {
            'total': total_notificaciones,
            'no_leidas': no_leidas,
            'leidas': leidas,
        }
    })
    
    return render(request, 'notifications/lista.html', context)

@session_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación específica como leída"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=usuario)
        notificacion.marcar_como_leida()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Notificación marcada como leída')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, 'Error al marcar la notificación como leída')
    
    return redirect('lista_notificaciones')

@session_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones del usuario como leídas"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    
    try:
        # Marcar todas las notificaciones no leídas como leídas
        notificaciones_no_leidas = usuario.notificaciones.filter(leida=False)
        cantidad_marcadas = notificaciones_no_leidas.update(leida=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'cantidad_marcadas': cantidad_marcadas
            })
        else:
            messages.success(request, f'{cantidad_marcadas} notificaciones marcadas como leídas')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, 'Error al marcar las notificaciones como leídas')
    
    return redirect('lista_notificaciones')

def finalizar_etapas(request, proyecto_id):
    proyecto = Proyecto.objects.get(id=proyecto_id)

    # Marcar el proyecto como listo (opcional)
    proyecto.estado = "Listo"
    proyecto.save()

    # Notificar a todos los usuarios
    usuarios = User.objects.exclude(id=request.session.get("user_id"))  # excluye al originador si querés
    for usuario in usuarios:
        Notificacion.objects.create(
            usuario=usuario,
            mensaje=f"Se ha creado un nuevo proyecto: '{proyecto.nombre}'",
            leida=False,
            url=f"/proyecto/detalle/{proyecto.id}/"
        )

    print("✅ Notificación enviada a todos los usuarios")
    return redirect("proyecto_lista")  # o cualquier vista general que uses

def crear_notificacion(usuario, mensaje, tipo='info', url=None):
    """
    Función helper para crear notificaciones programáticamente
    
    Args:
        usuario: Instancia del modelo User
        mensaje: Texto de la notificación
        tipo: 'info', 'warning', 'success', 'danger'
        url: URL opcional para redirigir
    
    Returns:
        Notificacion: La notificación creada
    """
    return Notificacion.objects.create(
        usuario=usuario,
        mensaje=mensaje,
        tipo=tipo,
        url=url,
        leida=False
    )