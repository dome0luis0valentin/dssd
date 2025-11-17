"""
Context processors para añadir datos globales a todos los templates
"""
from user.models import User
from notifications.models import Notificacion  # Ajustá el import según tu app


def user_menu_context(request):
    """
    Añade el contexto del usuario y menú de navegación a todos los templates
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return {
            'current_user': None,
            'user_role': None,
            'user_permissions': {},
            'navigation_menu': [],
        }
    
    try:
        from user.utils import get_user_role, get_user_permissions, get_navigation_menu
        usuario = User.objects.get(id=user_id)
        
        return {
            'current_user': usuario,
            'user_role': get_user_role(usuario),
            'user_permissions': get_user_permissions(usuario),
            'navigation_menu': get_navigation_menu(usuario),
        }
    except User.DoesNotExist:
        return {
            'current_user': None,
            'user_role': None,
            'user_permissions': {},
            'navigation_menu': [],
        }

def notificaciones_context(request):
    user_id = request.session.get("user_id")
    if user_id:
        try:
            usuario = User.objects.get(id=user_id)
            notificaciones = Notificacion.objects.filter(usuario=usuario, leida=False).order_by("-fecha")
            return {
                "notificaciones_no_leidas": notificaciones,
                "cantidad_notificaciones": notificaciones.count()
            }
        except User.DoesNotExist:
            pass
    return {
        "notificaciones_no_leidas": [],
        "cantidad_notificaciones": 0
    }
