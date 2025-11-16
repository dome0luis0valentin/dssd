from django.shortcuts import render, redirect
from django.db.models import Count, Q
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
        'en_proceso': Proyecto.objects.filter(estado='proceso').count(),
        'en_ejecucion': Proyecto.objects.filter(estado='ejecucion').count(),
        'finalizados': Proyecto.objects.filter(estado='finalizado').count(),
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
    
    # Proyectos de mi ONG
    mis_proyectos = Proyecto.objects.filter(originador=ong)
    
    # Estadísticas de mis proyectos
    mis_stats = {
        'total': mis_proyectos.count(),
        'en_proceso': mis_proyectos.filter(estado='proceso').count(),
        'en_ejecucion': mis_proyectos.filter(estado='ejecucion').count(),
        'finalizados': mis_proyectos.filter(estado='finalizado').count(),
    }
    
    # Proyectos recientes de mi ONG
    proyectos_recientes = mis_proyectos.order_by('-id')[:5]
    
    # Colaboraciones recibidas (compromisos en mis proyectos)
    from Commitment.models import Compromiso
    colaboraciones = Compromiso.objects.filter(
        pedido__etapas__proyecto__originador=ong
    ).distinct()[:5]
    
    return {
        'dashboard_type': 'ong_originante',
        'mis_stats': mis_stats,
        'proyectos_recientes': proyectos_recientes,
        'colaboraciones_recibidas': colaboraciones,
        'ong': ong,
    }

def _get_ong_colaboradora_dashboard_data(usuario):
    """Datos específicos para ONG colaboradora"""
    
    ong = usuario.ong
    
    # Compromisos de mi ONG
    from Commitment.models import Compromiso
    mis_compromisos = Compromiso.objects.filter(responsable=ong)
    
    # Estadísticas de compromisos
    compromisos_stats = {
        'total': mis_compromisos.count(),
        'pendientes': mis_compromisos.filter(pedido__estado=False).count(),
        'completados': mis_compromisos.filter(pedido__estado=True).count(),
    }
    
    # Proyectos en los que participamos
    proyectos_participando = Proyecto.objects.filter(
        etapas__pedido__compromisos__responsable=ong
    ).distinct()
    
    # Pedidos de colaboración disponibles
    from CoverageRequest.models import PedidoCobertura
    pedidos_disponibles = PedidoCobertura.objects.filter(
        estado=False,
        compromisos__isnull=True
    )[:5]
    
    return {
        'dashboard_type': 'ong_colaboradora',
        'compromisos_stats': compromisos_stats,
        'mis_compromisos': mis_compromisos[:5],
        'proyectos_participando': proyectos_participando[:5],
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
        # Consejo puede crear observaciones
        from Observation.models import Observacion
        todas_observaciones = Observacion.objects.all().order_by('-id')
        
        context.update({
            'puede_crear': True,
            'observaciones': todas_observaciones,
        })
    elif role in ['ong_originante', 'ong_colaboradora']:
        # ONGs pueden ver observaciones de sus proyectos
        from Observation.models import Observacion
        
        if role == 'ong_originante':
            # Ver observaciones de mis proyectos
            observaciones_mis_proyectos = Observacion.objects.filter(
                proyecto__originador=usuario.ong
            )
        else:
            # Ver observaciones de proyectos donde participo
            observaciones_mis_proyectos = Observacion.objects.filter(
                proyecto__etapas__pedido__compromisos__responsable=usuario.ong
            ).distinct()
        
        context.update({
            'puede_crear': False,
            'observaciones': observaciones_mis_proyectos,
        })
    
    return render(request, 'observaciones.html', context)

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
