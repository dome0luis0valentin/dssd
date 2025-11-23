from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib import messages
from Project.models import Proyecto
from user.models import User
from user.wraps import session_required
from user.utils import get_user_context
from ONG.models import ONG

def index(request):
    user_name = request.session.get("user_name")
    return render(request,'home.html',{"user_name": user_name})

@session_required
def dashboard(request):
    """
    Dashboard principal con vista personalizada según el rol del usuario
    """
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    role = user_context['user_role']
    
    # Datos base para todos los roles
    context = user_context.copy()
    
    if role == 'gerencial':
        # Dashboard gerencial - vista completa
        context.update(_get_gerencial_dashboard_data(usuario))
    elif role == 'ong_originante':
        # Dashboard para ONG originante
        context.update(_get_ong_originante_dashboard_data(usuario))
    elif role == 'ong_colaboradora':
        # Dashboard para ONG colaboradora
        context.update(_get_ong_colaboradora_dashboard_data(usuario))
    
    return render(request, "dashboard.html", context)

def _get_gerencial_dashboard_data(usuario):
    """Datos específicos para el dashboard gerencial"""
    
    # Estadísticas generales de proyectos
    proyectos_stats = {
        'total': Proyecto.objects.count(),
        'en_proceso': Proyecto.objects.filter(estado='Proceso').count(),
        'en_ejecucion': Proyecto.objects.filter(estado='Ejecucion').count(),
        'finalizados': Proyecto.objects.filter(estado='Finalizado').count(),
    }
    
    # Proyectos recientes
    proyectos_recientes = Proyecto.objects.all().order_by('-id')[:5]
    
    # Distribución por estado
    proyectos_por_estado = list(
        Proyecto.objects.values('estado')
        .annotate(count=Count('estado'))
        .order_by('estado')
    )
    
    # ONGs más activas
    from ONG.models import ONG
    ongs_activas = list(
        ONG.objects.annotate(
            proyectos_count=Count('proyectos_originados')
        ).order_by('-proyectos_count')[:5]
    )
    
    return {
        'dashboard_type': 'gerencial',
        'proyectos_stats': proyectos_stats,
        'proyectos_recientes': proyectos_recientes,
        'proyectos_por_estado': proyectos_por_estado,
        'ongs_activas': ongs_activas,
    }

def _get_ong_originante_dashboard_data(usuario):
    """Datos específicos para ONG originante"""
    
    ong = usuario.ong
    
    # Proyectos de mi ONG con información detallada
    from Stage.models import Etapa
    from Commitment.models import Compromiso
    from Observation.models import Observacion
    
    mis_proyectos = Proyecto.objects.filter(originador=ong)
    
    # Estadísticas de mis proyectos
    mis_stats = {
        'total': mis_proyectos.count(),
        'en_proceso': mis_proyectos.filter(estado='Proceso').count(),
        'en_ejecucion': mis_proyectos.filter(estado='ejecucion').count(),
        'finalizados': mis_proyectos.filter(estado='finalizado').count(),
    }
    
    # Proyectos recientes con información completa
    proyectos_detallados = []
    for proyecto in mis_proyectos.order_by('-id')[:10]:
        # Calcular progreso del proyecto
        etapas_total = proyecto.etapas.count()
        etapas_completadas = proyecto.etapas.filter(pedido__estado=True).count()
        progreso_porcentaje = (etapas_completadas / etapas_total * 100) if etapas_total > 0 else 0
        
        # Solicitudes de colaboración pendientes
        solicitudes_pendientes = proyecto.etapas.filter(
            pedido__estado=False,
            pedido__compromisos__isnull=True
        ).count()
        
        # Colaboraciones activas
        colaboraciones_activas = Compromiso.objects.filter(
            pedido__etapas__proyecto=proyecto
        ).count()
        
        # Observaciones del proyecto
        observaciones_count = proyecto.observaciones.count()
        
        proyectos_detallados.append({
            'proyecto': proyecto,
            'etapas_total': etapas_total,
            'etapas_completadas': etapas_completadas,
            'progreso_porcentaje': round(progreso_porcentaje, 1),
            'solicitudes_pendientes': solicitudes_pendientes,
            'colaboraciones_activas': colaboraciones_activas,
            'observaciones_count': observaciones_count,
        })
    
    # Colaboraciones recibidas (compromisos en mis proyectos)
    colaboraciones_recibidas = Compromiso.objects.filter(
        pedido__etapas__proyecto__originador=ong
    ).distinct().select_related('responsable', 'pedido')[:5]
    
    # Solicitudes de colaboración pendientes
    solicitudes_colaboracion = Etapa.objects.filter(
        proyecto__originador=ong,
        pedido__estado=False,
        pedido__compromisos__isnull=True
    ).select_related('proyecto', 'pedido__tipo_cobertura')[:5]
    
    return {
        'dashboard_type': 'ong_originante',
        'mis_stats': mis_stats,
        'proyectos_detallados': proyectos_detallados,
        'colaboraciones_recibidas': colaboraciones_recibidas,
        'solicitudes_colaboracion': solicitudes_colaboracion,
        'ong': ong,
    }

def _get_ong_colaboradora_dashboard_data(usuario):
    """Datos específicos para ONG colaboradora"""
    
    ong = usuario.ong
    
    # Compromisos de mi ONG con información detallada
    from Commitment.models import Compromiso
    from Stage.models import Etapa
    from Observation.models import Observacion
    
    mis_compromisos = Compromiso.objects.filter(responsable=ong)
    
    # Estadísticas de compromisos
    compromisos_stats = {
        'total': mis_compromisos.count(),
        'pendientes': mis_compromisos.filter(pedido__estado=False).count(),
        'completados': mis_compromisos.filter(pedido__estado=True).count(),
    }
    
    # Proyectos en los que participamos con detalles de progreso
    proyectos_colaborando = []
    proyectos_participando = Proyecto.objects.filter(
        etapas__pedido__compromisos__responsable=ong
    ).distinct()
    
    for proyecto in proyectos_participando[:10]:
        # Mis tareas en este proyecto
        mis_tareas = mis_compromisos.filter(
            pedido__etapas__proyecto=proyecto
        )
        
        tareas_total = mis_tareas.count()
        tareas_completadas = mis_tareas.filter(pedido__estado=True).count()
        progreso_mis_tareas = (tareas_completadas / tareas_total * 100) if tareas_total > 0 else 0
        
        # Progreso general del proyecto
        etapas_total = proyecto.etapas.count()
        etapas_completadas = proyecto.etapas.filter(pedido__estado=True).count()
        progreso_general = (etapas_completadas / etapas_total * 100) if etapas_total > 0 else 0
        
        # Observaciones del proyecto
        observaciones_count = proyecto.observaciones.count()
        
        # Estado de mis compromisos específicos
        compromisos_pendientes = mis_tareas.filter(pedido__estado=False).count()
        
        proyectos_colaborando.append({
            'proyecto': proyecto,
            'tareas_total': tareas_total,
            'tareas_completadas': tareas_completadas,
            'progreso_mis_tareas': round(progreso_mis_tareas, 1),
            'progreso_general': round(progreso_general, 1),
            'observaciones_count': observaciones_count,
            'compromisos_pendientes': compromisos_pendientes,
            'estado_participacion': 'Activa' if compromisos_pendientes > 0 else 'Completada'
        })
    
    # Compromisos detallados con estado
    compromisos_detallados = []
    for compromiso in mis_compromisos.select_related('pedido__tipo_cobertura')[:10]:
        etapa = compromiso.pedido.etapas.first()
        proyecto = etapa.proyecto if etapa else None
        
        compromisos_detallados.append({
            'compromiso': compromiso,
            'proyecto': proyecto,
            'etapa': etapa,
            'estado': 'Completado' if compromiso.pedido.estado else 'Pendiente',
            'tipo_cobertura': compromiso.pedido.tipo_cobertura.nombre,
        })
    
    # Pedidos de colaboración disponibles
    from CoverageRequest.models import PedidoCobertura
    pedidos_disponibles = PedidoCobertura.objects.filter(
        estado=False,
        compromisos__isnull=True
    ).select_related('tipo_cobertura')[:5]
    
    return {
        'dashboard_type': 'ong_colaboradora',
        'compromisos_stats': compromisos_stats,
        'proyectos_colaborando': proyectos_colaborando,
        'compromisos_detallados': compromisos_detallados,
        'pedidos_disponibles': pedidos_disponibles,
        'ong': ong,
    }

@session_required
def mis_colaboraciones(request):
    """Vista para mostrar las colaboraciones disponibles para una ONG"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    
    # Solo ONGs colaboradoras pueden ver esta página
    if not usuario.ong or user_context['user_role'] not in ['ong_colaboradora', 'ong_originante']:
        return redirect('dashboard')
    
    # Pedidos de colaboración disponibles (sin compromiso)
    from CoverageRequest.models import PedidoCobertura
    pedidos_disponibles = PedidoCobertura.objects.filter(
        estado=False,
        compromisos__isnull=True
    )
    
    # Proyectos en los que ya participa esta ONG
    proyectos_participando = Proyecto.objects.filter(
        etapas__pedido__compromisos__responsable=usuario.ong
    ).distinct()
    
    context = user_context.copy()
    context.update({
        'pedidos_disponibles': pedidos_disponibles,
        'proyectos_participando': proyectos_participando,
    })
    
    return render(request, 'colaboraciones.html', context)

@session_required
def mis_compromisos(request):
    """Vista para mostrar los compromisos activos del usuario"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    
    if not usuario.ong:
        return redirect('dashboard')
    
    # Compromisos de mi ONG
    from Commitment.models import Compromiso
    compromisos_activos = Compromiso.objects.filter(responsable=usuario.ong)
    
    context = user_context.copy()
    context.update({
        'compromisos_activos': compromisos_activos,
    })
    
    return render(request, 'mis_compromisos.html', context)

@session_required
def observaciones(request):
    """Vista para gestionar observaciones (crear/ver según rol)"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    role = user_context['user_role']
    
    context = user_context.copy()
    
    if role == 'gerencial':
        # Redirigir a la interface gerencial completa
        return redirect('interface_gerencial')
    elif role in ['ong_originante', 'ong_colaboradora']:
        # ONGs pueden ver observaciones de sus proyectos
        from Observation.models import Observacion
        
        if role == 'ong_originante':
            # Ver observaciones de mis proyectos con estadísticas
            observaciones_mis_proyectos = Observacion.objects.filter(
                proyecto__originador=usuario.ong
            ).select_related('proyecto', 'consejo').order_by('-fecha_creacion')
            
            # Estadísticas para ONG originante
            total_observaciones = observaciones_mis_proyectos.count()
            observaciones_pendientes = observaciones_mis_proyectos.filter(estado='pendiente').count()
            observaciones_resueltas = observaciones_mis_proyectos.filter(estado='resuelta').count()
            
        else:
            # Ver observaciones de proyectos donde participo
            observaciones_mis_proyectos = Observacion.objects.filter(
                proyecto__etapas__pedido__compromisos__responsable=usuario.ong
            ).select_related('proyecto', 'consejo').distinct().order_by('-fecha_creacion')
            
            # Estadísticas para ONG colaboradora
            total_observaciones = observaciones_mis_proyectos.count()
            observaciones_pendientes = observaciones_mis_proyectos.filter(estado='pendiente').count()
            observaciones_resueltas = observaciones_mis_proyectos.filter(estado='resuelta').count()
        
        # Proyectos únicos con observaciones
        proyectos_con_observaciones = observaciones_mis_proyectos.values_list('proyecto', flat=True).distinct()
        cantidad_proyectos = len(set(proyectos_con_observaciones))
        
        context.update({
            'puede_crear': False,
            'puede_resolver': role == 'ong_originante',  # Solo originantes pueden resolver
            'observaciones': observaciones_mis_proyectos,
            'estadisticas': {
                'total_observaciones': total_observaciones,
                'observaciones_pendientes': observaciones_pendientes,
                'observaciones_resueltas': observaciones_resueltas,
                'proyectos_con_observaciones': cantidad_proyectos,
            }
        })
    
    return render(request, 'observaciones.html', context)

@session_required
def interface_gerencial(request):
    """Interface gerencial para seleccionar proyectos y crear observaciones"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    # Solo usuarios gerenciales pueden acceder
    if user_context['user_role'] != 'gerencial':
        return redirect('dashboard')
    
    from Stage.models import Etapa
    from Observation.models import Observacion
    
    # Obtener todos los proyectos en progreso
    proyectos_en_progreso = Proyecto.objects.filter(
        estado__in=['Proceso', 'Ejecucion']
    ).select_related('originador').prefetch_related('etapas', 'observaciones')
    
    # Estadísticas para el header
    total_proyectos = proyectos_en_progreso.count()
    proyectos_proceso = proyectos_en_progreso.filter(estado='Proceso').count()
    proyectos_ejecucion = proyectos_en_progreso.filter(estado='ejecucion').count()
    total_observaciones = Observacion.objects.count()
    
    # Preparar información detallada de cada proyecto
    proyectos_detalle = []
    for proyecto in proyectos_en_progreso:
        etapas = proyecto.etapas.all()
        etapas_total = etapas.count()
        etapas_completadas = etapas.filter(pedido__estado=True).count()
        observaciones_count = proyecto.observaciones.count()
        
        # Obtener colaboradores únicos
        from Commitment.models import Compromiso
        colaboradores = Compromiso.objects.filter(
            pedido__etapas__proyecto=proyecto
        ).select_related('responsable').distinct()
        
        proyectos_detalle.append({
            'proyecto': proyecto,
            'etapas_total': etapas_total,
            'etapas_completadas': etapas_completadas,
            'progreso_porcentaje': (etapas_completadas / etapas_total * 100) if etapas_total > 0 else 0,
            'observaciones_count': observaciones_count,
            'colaboradores': colaboradores,
            'ultima_observacion': proyecto.observaciones.order_by('-id').first(),
        })
    
    context = user_context.copy()
    context.update({
        'proyectos_detalle': proyectos_detalle,
        'stats': {
            'total_proyectos': total_proyectos,
            'proyectos_proceso': proyectos_proceso,
            'proyectos_ejecucion': proyectos_ejecucion,
            'total_observaciones': total_observaciones,
        }
    })
    
    return render(request, 'interface_gerencial.html', context)

@session_required
def detalle_proyecto_gerencial(request, proyecto_id):
    """Vista detallada de proyecto para usuario gerencial con todas las actividades"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    # Solo usuarios gerenciales pueden acceder
    if user_context['user_role'] != 'gerencial':
        return redirect('dashboard')
    
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return redirect('interface_gerencial')
    
    from Stage.models import Etapa
    from Commitment.models import Compromiso
    from Observation.models import Observacion
    
    # Obtener todas las etapas/actividades del proyecto
    etapas = proyecto.etapas.all().order_by('fecha_inicio')
    
    # Preparar información detallada de cada etapa
    etapas_detalle = []
    for etapa in etapas:
        etapa_info = {
            'etapa': etapa,
            'compromisos': [],
            'estado': 'Sin solicitar',
            'observaciones': [],
        }
        
        if etapa.pedido:
            compromisos = etapa.pedido.compromisos.all().select_related('responsable')
            etapa_info['estado'] = 'Completado' if etapa.pedido.estado else ('Con colaborador' if compromisos.exists() else 'Solicitando colaboración')
            etapa_info['tipo_cobertura'] = etapa.pedido.tipo_cobertura.nombre
            etapa_info['compromisos'] = compromisos
        
        # Obtener observaciones específicas de esta etapa (si las hay)
        # Por ahora las observaciones son a nivel proyecto, pero podríamos extender
        etapas_detalle.append(etapa_info)
    
    # Todas las observaciones del proyecto
    observaciones = proyecto.observaciones.all().select_related('consejo').order_by('-id')
    
    # Estadísticas del proyecto
    etapas_total = etapas.count()
    etapas_completadas = etapas.filter(pedido__estado=True).count()
    progreso_porcentaje = (etapas_completadas / etapas_total * 100) if etapas_total > 0 else 0
    
    # Colaboradores únicos del proyecto
    colaboradores_unicos = Compromiso.objects.filter(
        pedido__etapas__proyecto=proyecto
    ).select_related('responsable').distinct()
    
    context = user_context.copy()
    context.update({
        'proyecto': proyecto,
        'etapas_detalle': etapas_detalle,
        'observaciones': observaciones,
        'etapas_total': etapas_total,
        'etapas_completadas': etapas_completadas,
        'progreso_porcentaje': round(progreso_porcentaje, 1),
        'colaboradores_unicos': colaboradores_unicos,
    })
    
    return render(request, 'detalle_proyecto_gerencial.html', context)

@session_required
def crear_observacion(request, proyecto_id, etapa_id=None):
    """Crear una nueva observación para un proyecto o etapa específica"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    # Solo usuarios gerenciales pueden crear observaciones
    if user_context['user_role'] != 'gerencial':
        return redirect('dashboard')
    
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return redirect('interface_gerencial')
    
    etapa = None
    if etapa_id:
        try:
            from Stage.models import Etapa
            etapa = Etapa.objects.get(id=etapa_id, proyecto=proyecto)
        except Etapa.DoesNotExist:
            pass
    
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        
        if descripcion:
            from Observation.models import Observacion
            
            # Crear la observación
            observacion = Observacion.objects.create(
                proyecto=proyecto,
                consejo=user_context['consejo'],
                descripcion=descripcion
            )
            
            messages.success(request, f'Observación creada exitosamente para el proyecto "{proyecto.nombre}"')
            return redirect('detalle_proyecto_gerencial', proyecto_id=proyecto.id)
        else:
            messages.error(request, 'La descripción de la observación no puede estar vacía')
    
    context = user_context.copy()
    context.update({
        'proyecto': proyecto,
        'etapa': etapa,
    })
    
    return render(request, 'crear_observacion.html', context)

@session_required 
def dashboard_gerencial(request):
    """Dashboard específico para usuarios gerenciales con métricas avanzadas"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    # Solo usuarios gerenciales pueden acceder
    if user_context['user_role'] != 'gerencial':
        return redirect('dashboard')
    
    # Métricas avanzadas para gerencia
    from ONG.models import ONG
    from Observation.models import Observacion
    from Commitment.models import Compromiso
    
    # Consulta 1: Proyectos por ONG con estadísticas
    proyectos_por_ong = list(
        ONG.objects.annotate(
            total_proyectos=Count('proyectos_originados'),
            proyectos_activos=Count('proyectos_originados', filter=Q(proyectos_originados__estado__in=['proceso', 'ejecucion'])),
            proyectos_finalizados=Count('proyectos_originados', filter=Q(proyectos_originados__estado='finalizado'))
        ).order_by('-total_proyectos')
    )
    
    # Consulta 2: Observaciones por resolver (últimos 30 días)
    from django.utils import timezone
    from datetime import timedelta
    fecha_limite = timezone.now() - timedelta(days=30)
    
    observaciones_recientes = Observacion.objects.filter(
        # Asumiendo que tienes un campo fecha_creacion
    ).count()
    
    # Consulta 3: Compromisos por estado
    compromisos_stats = {
        'total': Compromiso.objects.count(),
        'pendientes': Compromiso.objects.filter(pedido__estado=False).count(),
        'completados': Compromiso.objects.filter(pedido__estado=True).count(),
    }
    
    context = user_context.copy()
    context.update({
        'proyectos_por_ong': proyectos_por_ong,
        'observaciones_recientes': observaciones_recientes,
        'compromisos_stats': compromisos_stats,
    })
    
    return render(request, 'dashboard_gerencial.html', context)

@session_required
def panel_seguimiento(request):
    """Panel de seguimiento completo para organizaciones"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    role = user_context['user_role']
    
    # Solo ONGs pueden acceder al panel de seguimiento
    if not usuario.ong or role == 'gerencial':
        return redirect('dashboard')
    
    from Stage.models import Etapa
    from Commitment.models import Compromiso
    from Observation.models import Observacion
    
    ong = usuario.ong
    context = user_context.copy()
    
    if role == 'ong_originante':
        # Panel para ONG originante - seguimiento de sus proyectos
        mis_proyectos = Proyecto.objects.filter(originador=ong)
        
        proyectos_seguimiento = []
        for proyecto in mis_proyectos:
            # Detalles completos del proyecto
            etapas = proyecto.etapas.all()
            etapas_total = etapas.count()
            etapas_completadas = etapas.filter(pedido__estado=True).count()
            
            # Colaboradores por etapa
            colaboradores = {}
            solicitudes_pendientes = []
            
            for etapa in etapas:
                if etapa.pedido:
                    compromisos = etapa.pedido.compromisos.all()
                    if compromisos.exists():
                        colaboradores[etapa.nombre] = [c.responsable for c in compromisos]
                    else:
                        solicitudes_pendientes.append({
                            'etapa': etapa.nombre,
                            'tipo_cobertura': etapa.pedido.tipo_cobertura.nombre,
                            'fecha_inicio': etapa.fecha_inicio,
                        })
            
            # Observaciones del proyecto
            observaciones = proyecto.observaciones.all()
            
            proyectos_seguimiento.append({
                'proyecto': proyecto,
                'etapas_total': etapas_total,
                'etapas_completadas': etapas_completadas,
                'progreso_porcentaje': (etapas_completadas / etapas_total * 100) if etapas_total > 0 else 0,
                'colaboradores': colaboradores,
                'solicitudes_pendientes': solicitudes_pendientes,
                'observaciones': observaciones,
                'observaciones_count': observaciones.count(),
            })
        
        context.update({
            'panel_tipo': 'originante',
            'proyectos_seguimiento': proyectos_seguimiento,
        })
        
    elif role == 'ong_colaboradora':
        # Panel para ONG colaboradora - seguimiento de participaciones
        mis_compromisos = Compromiso.objects.filter(responsable=ong)
        
        participaciones_seguimiento = []
        proyectos_participando = Proyecto.objects.filter(
            etapas__pedido__compromisos__responsable=ong
        ).distinct()
        
        for proyecto in proyectos_participando:
            # Mis compromisos en este proyecto
            compromisos_proyecto = mis_compromisos.filter(
                pedido__etapas__proyecto=proyecto
            )
            
            tareas_total = compromisos_proyecto.count()
            tareas_completadas = compromisos_proyecto.filter(pedido__estado=True).count()
            
            # Estado detallado de cada compromiso
            compromisos_detalle = []
            for compromiso in compromisos_proyecto:
                etapa = compromiso.pedido.etapas.first()
                compromisos_detalle.append({
                    'compromiso': compromiso,
                    'etapa': etapa.nombre if etapa else 'Sin etapa',
                    'tipo_cobertura': compromiso.pedido.tipo_cobertura.nombre,
                    'estado': 'Completado' if compromiso.pedido.estado else 'Pendiente',
                    'fecha_inicio': compromiso.fecha_inicio,
                    'fecha_fin': compromiso.fecha_fin,
                })
            
            # Progreso general del proyecto
            etapas_total_proyecto = proyecto.etapas.count()
            etapas_completadas_proyecto = proyecto.etapas.filter(pedido__estado=True).count()
            
            # Observaciones del proyecto
            observaciones = proyecto.observaciones.all()
            
            participaciones_seguimiento.append({
                'proyecto': proyecto,
                'originador': proyecto.originador,
                'mis_tareas_total': tareas_total,
                'mis_tareas_completadas': tareas_completadas,
                'mi_progreso': (tareas_completadas / tareas_total * 100) if tareas_total > 0 else 0,
                'progreso_general': (etapas_completadas_proyecto / etapas_total_proyecto * 100) if etapas_total_proyecto > 0 else 0,
                'compromisos_detalle': compromisos_detalle,
                'observaciones': observaciones,
                'observaciones_count': observaciones.count(),
                'estado_participacion': 'Activa' if tareas_total > tareas_completadas else 'Completada'
            })
        
        context.update({
            'panel_tipo': 'colaboradora',
            'participaciones_seguimiento': participaciones_seguimiento,
        })
    
    return render(request, 'panel_seguimiento.html', context)

@session_required
def detalle_proyecto_seguimiento(request, proyecto_id):
    """Vista detallada de seguimiento para un proyecto específico"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    role = user_context['user_role']
    
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return redirect('panel_seguimiento')
    
    # Verificar permisos
    if role == 'ong_originante' and proyecto.originador != usuario.ong:
        return redirect('panel_seguimiento')
    elif role == 'ong_colaboradora':
        # Verificar que tenga compromisos en el proyecto
        from Commitment.models import Compromiso
        if not Compromiso.objects.filter(
            responsable=usuario.ong,
            pedido__etapas__proyecto=proyecto
        ).exists():
            return redirect('panel_seguimiento')
    
    # Obtener información detallada del proyecto
    from Stage.models import Etapa
    from Commitment.models import Compromiso
    from Observation.models import Observacion
    
    etapas = proyecto.etapas.all().order_by('fecha_inicio')
    
    etapas_detalle = []
    for etapa in etapas:
        etapa_info = {
            'etapa': etapa,
            'compromisos': [],
            'estado': 'Sin solicitar'
        }
        
        if etapa.pedido:
            compromisos = etapa.pedido.compromisos.all()
            etapa_info['estado'] = 'Completado' if etapa.pedido.estado else ('Con colaborador' if compromisos.exists() else 'Solicitando colaboración')
            etapa_info['tipo_cobertura'] = etapa.pedido.tipo_cobertura.nombre
            
            for compromiso in compromisos:
                etapa_info['compromisos'].append({
                    'compromiso': compromiso,
                    'responsable': compromiso.responsable,
                    'tipo': compromiso.get_tipo_display(),
                    'estado': 'Completado' if compromiso.pedido.estado else 'En progreso'
                })
        
        etapas_detalle.append(etapa_info)
    
    # Observaciones del proyecto
    observaciones = proyecto.observaciones.all().order_by('-id')
    
    # Estadísticas
    etapas_total = etapas.count()
    etapas_completadas = etapas.filter(pedido__estado=True).count()
    progreso_porcentaje = (etapas_completadas / etapas_total * 100) if etapas_total > 0 else 0
    
    context = user_context.copy()
    context.update({
        'proyecto': proyecto,
        'etapas_detalle': etapas_detalle,
        'observaciones': observaciones,
        'etapas_total': etapas_total,
        'etapas_completadas': etapas_completadas,
        'progreso_porcentaje': round(progreso_porcentaje, 1),
        'puede_editar': role == 'ong_originante' and proyecto.originador == usuario.ong,
    })
    
    return render(request, 'detalle_proyecto_seguimiento.html', context)

@session_required
def reportes(request):
    """Vista para generar reportes gerenciales"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    # Solo usuarios gerenciales pueden ver reportes
    if user_context['user_role'] != 'gerencial':
        return redirect('dashboard')
    
    # Datos para reportes
    from django.db.models import Count, Avg
    
    # Reporte 1: Eficiencia por ONG
    eficiencia_ongs = list(
        ONG.objects.annotate(
            total_compromisos=Count('compromisos_responsables'),
            compromisos_completados=Count('compromisos_responsables', filter=Q(compromisos_responsables__pedido__estado=True))
        ).exclude(total_compromisos=0)
    )
    
    # Añadir cálculo de porcentaje
    for ong in eficiencia_ongs:
        if ong.total_compromisos > 0:
            ong.porcentaje_eficiencia = (ong.compromisos_completados / ong.total_compromisos) * 100
        else:
            ong.porcentaje_eficiencia = 0
    
    context = user_context.copy()
    context.update({
        'eficiencia_ongs': eficiencia_ongs,
    })
    
    return render(request, 'reportes.html', context)

@session_required
def marcar_observacion_resuelta(request, observacion_id):
    """Marca una observación como resuelta"""
    user_context = get_user_context(request)
    if not user_context:
        return redirect("login")
    
    usuario = user_context['usuario']
    role = user_context['user_role']
    
    try:
        from Observation.models import Observacion
        observacion = Observacion.objects.get(id=observacion_id)
        
        # Verificar permisos - solo ONGs originantes pueden marcar como resueltas las observaciones de sus proyectos
        if role == 'ong_originante' and observacion.proyecto.originador == usuario.ong:
            observacion.marcar_como_resuelta()
            messages.success(request, f'Observación marcada como resuelta para el proyecto "{observacion.proyecto.nombre}"')
        else:
            messages.error(request, 'No tienes permisos para marcar esta observación como resuelta')
            
    except Observacion.DoesNotExist:
        messages.error(request, 'La observación no existe')
    
    return redirect('observaciones')
