"""
Utilities para manejar roles de usuario y permisos
"""

def get_user_role(user):
    """
    Determina el rol principal del usuario basado en sus relaciones
    
    Returns:
        str: 'ong_originante', 'ong_colaboradora', 'gerencial', 'sin_rol'
    """
    if user.consejo:
        return 'gerencial'
    elif user.ong:
        # Verificar si es originante (tiene proyectos creados)
        if hasattr(user.ong, 'proyectos_originados') and user.ong.proyectos_originados.exists():
            return 'ong_originante'
        else:
            return 'ong_colaboradora'
    else:
        return 'sin_rol'

def get_user_permissions(user):
    """
    Retorna los permisos del usuario basado en su rol
    
    Returns:
        dict: diccionario con permisos booleanos
    """
    role = get_user_role(user)
    
    permissions = {
        'can_create_projects': False,
        'can_view_all_projects': False,
        'can_participate_projects': False,
        'can_manage_commitments': False,
        'can_view_observations': False,
        'can_create_observations': False,
        'can_view_dashboard': False,
        'can_view_reports': False,
    }
    
    if role == 'gerencial':
        permissions.update({
            'can_view_all_projects': True,
            'can_create_observations': True,
            'can_view_dashboard': True,
            'can_view_reports': True,
        })
    elif role == 'ong_originante':
        permissions.update({
            'can_create_projects': True,
            'can_view_all_projects': True,
            'can_manage_commitments': True,
            'can_view_observations': True,
        })
    elif role == 'ong_colaboradora':
        permissions.update({
            'can_view_all_projects': True,
            'can_participate_projects': True,
            'can_manage_commitments': True,
        })
    
    return permissions

def get_navigation_menu(user):
    """
    Retorna el menú de navegación específico para el rol del usuario
    
    Returns:
        list: lista de diccionarios con items del menú
    """
    role = get_user_role(user)
    permissions = get_user_permissions(user)
    
    menu_items = []
    
    # Menú común para todos
    menu_items.append({
        'label': 'Inicio',
        'url': 'home',
        'icon': 'bi-house',
        'active': False
    })
    
    menu_items.append({
        'label': 'Dashboard',
        'url': 'dashboard',
        'icon': 'bi-speedometer2',
        'active': False
    })
    
    if permissions['can_view_all_projects']:
        menu_items.append({
            'label': 'Proyectos',
            'url': 'proyecto',
            'icon': 'bi-folder',
            'active': False
        })
    
    if permissions['can_create_projects']:
        menu_items.append({
            'label': 'Crear Proyecto',
            'url': 'crear_proyecto',
            'icon': 'bi-plus-circle',
            'active': False
        })
    
    # Solo añadir URLs que existen para evitar errores
    from django.urls import reverse, NoReverseMatch
    
    def safe_add_menu_item(items_list, item_dict):
        """Helper para añadir items del menú solo si la URL existe"""
        try:
            # Probar si la URL existe
            reverse(item_dict['url'])
            items_list.append(item_dict)
        except NoReverseMatch:
            # URL no existe, no añadir al menú
            pass
    
    if permissions['can_participate_projects']:
        safe_add_menu_item(menu_items, {
            'label': 'Colaboraciones',
            'url': 'mis_colaboraciones',
            'icon': 'bi-handshake',
            'active': False
        })
    
    if permissions['can_manage_commitments']:
        safe_add_menu_item(menu_items, {
            'label': 'Mis Compromisos',
            'url': 'mis_compromisos',
            'icon': 'bi-check-circle',
            'active': False
        })
    
    # Panel de seguimiento para ONGs
    if role in ['ong_originante', 'ong_colaboradora']:
        safe_add_menu_item(menu_items, {
            'label': 'Panel de Seguimiento',
            'url': 'panel_seguimiento',
            'icon': 'bi-clipboard-data',
            'active': False
        })
    
    if permissions['can_view_observations']:
        safe_add_menu_item(menu_items, {
            'label': 'Observaciones',
            'url': 'observaciones',
            'icon': 'bi-eye',
            'active': False
        })
    
    # Interface gerencial para crear observaciones
    if permissions['can_create_observations']:
        safe_add_menu_item(menu_items, {
            'label': 'Interface Gerencial',
            'url': 'interface_gerencial',
            'icon': 'bi-shield-check',
            'active': False
        })
    
    if permissions['can_view_dashboard']:
        safe_add_menu_item(menu_items, {
            'label': 'Dashboard Gerencial',
            'url': 'dashboard_gerencial',
            'icon': 'bi-graph-up',
            'active': False
        })
    
    if permissions['can_view_reports']:
        safe_add_menu_item(menu_items, {
            'label': 'Reportes',
            'url': 'reportes',
            'icon': 'bi-file-earmark-text',
            'active': False
        })
    
    return menu_items

def get_user_context(request):
    """
    Función helper para obtener contexto del usuario logueado
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    try:
        from user.models import User
        usuario = User.objects.get(id=user_id)
        
        # Obtener notificaciones no leídas para el header
        notificaciones_no_leidas = usuario.notificaciones.filter(leida=False).order_by('-fecha')[:5]
        cantidad_notificaciones = usuario.notificaciones.filter(leida=False).count()
        
        return {
            "current_user": usuario,
            "usuario": usuario,
            "consejo": usuario.consejo,
            "ong": usuario.ong,
            "user_role": get_user_role(usuario),
            "user_permissions": get_user_permissions(usuario),
            "navigation_menu": get_navigation_menu(usuario),
            "notificaciones_no_leidas": notificaciones_no_leidas,
            "cantidad_notificaciones": cantidad_notificaciones,
        }
    except User.DoesNotExist:
        return None
