from django.shortcuts import render, redirect, get_object_or_404
from .models import Etapa
from .forms import EtapaForm
from Project.models import Proyecto
import json
import requests

url_bonita = "http://localhost:8080/bonita"

def verificar_datos_bonita(case_id, cookies, headers, proyecto_nombre=None):
    """
    Función para verificar si los datos se guardaron correctamente en Bonita
    """
    print("🔍 === VERIFICACIÓN DE DATOS EN BONITA ===")
    
    try:
        # 1. Consultar variables del caso usando el endpoint correcto
        variables_url = f"{url_bonita}/API/bpm/caseVariable"
        var_params = {
            'p': 0,
            'c': 50,  # Máximo 50 variables
            'f': f'case_id={case_id}'  # Filtrar por case_id
        }
        var_resp = requests.get(variables_url, params=var_params, cookies=cookies, headers=headers, timeout=15)
        
        if var_resp.status_code == 200:
            variables_data = var_resp.json()
            print(f"📊 Variables del proceso ({len(variables_data)}):")
            for var in variables_data:
                print(f"   - {var.get('name')}: {var.get('value')} (tipo: {var.get('type')})")
        else:
            print(f"⚠️ Error al obtener variables con caseVariable: {var_resp.status_code}")
            
            # Intentar con processInstanceVariable como alternativa
            try:
                alt_var_url = f"{url_bonita}/API/bpm/processInstanceVariable"
                alt_params = {
                    'p': 0,
                    'c': 50,
                    'f': f'case_id={case_id}'
                }
                alt_resp = requests.get(alt_var_url, params=alt_params, cookies=cookies, headers=headers, timeout=15)
                
                if alt_resp.status_code == 200:
                    alt_variables = alt_resp.json()
                    print(f"📊 Variables del proceso (alternativo - {len(alt_variables)}):")
                    for var in alt_variables:
                        print(f"   - {var.get('name')}: {var.get('value')} (tipo: {var.get('type')})")
                else:
                    print(f"⚠️ Error también con processInstanceVariable: {alt_resp.status_code} - {alt_resp.text}")
            except Exception as alt_e:
                print(f"❌ Error en consulta alternativa: {alt_e}")
        
        # 1.5 Intentar obtener variables específicas que sabemos que existen
        print("🎯 Intentando obtener variables específicas:")
        variables_conocidas = ['cubierto', 'entregados', 'proyectoInput', 'proyectoBDMInput']
        for var_name in variables_conocidas:
            obtener_variable_especifica_bonita(case_id, var_name, cookies, headers)
        
        # 2. Consultar Business Objects (BDM) con función mejorada
        consultar_bdm_con_query_correcta(case_id, cookies, headers, proyecto_nombre)
        
        # 3. Estado del proceso
        process_url = f"{url_bonita}/API/bpm/case/{case_id}"
        proc_resp = requests.get(process_url, cookies=cookies, headers=headers, timeout=15)
        
        if proc_resp.status_code == 200:
            proc_data = proc_resp.json()
            print(f"🔄 Estado del proceso: {proc_data.get('state')}")
            print(f"📅 Iniciado: {proc_data.get('start')}")
            print(f"👤 Iniciado por: {proc_data.get('started_by')}")
        else:
            print(f"⚠️ Error consultando proceso: {proc_resp.status_code}")
            
        # 4. Consultar tareas activas del proceso
        tasks_url = f"{url_bonita}/API/bpm/humanTask"
        tasks_params = {'p': 0, 'c': 10, 'f': f'caseId={case_id}'}
        tasks_resp = requests.get(tasks_url, params=tasks_params, cookies=cookies, headers=headers, timeout=15)
        
        if tasks_resp.status_code == 200:
            tasks_data = tasks_resp.json()
            print(f"📋 Tareas activas ({len(tasks_data)}):")
            for task in tasks_data:
                print(f"   - {task.get('displayName')} (ID: {task.get('id')})")
                print(f"     Estado: {task.get('state')}")
                print(f"     Asignado a: {task.get('assigned_id', 'No asignado')}")
        else:
            print(f"⚠️ Error consultando tareas: {tasks_resp.status_code}")
            
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
    
    print("🔍 === FIN VERIFICACIÓN ===")
    return True

def buscar_tarea_por_nombre(case_id, task_name, cookies, headers):
    """
    Busca una tarea específica por nombre en un caso de Bonita
    """
    print(f"🔍 Buscando tarea '{task_name}' en caso {case_id}")
    
    try:
        # Buscar tareas humanas usando el endpoint correcto
        tasks_url = f"{url_bonita}/API/bpm/humanTask"
        tasks_params = {
            'p': 0,
            'c': 50,
            'f': f'caseId={case_id}'  # Filtrar por caseId
        }
        
        tasks_resp = requests.get(tasks_url, params=tasks_params, cookies=cookies, headers=headers, timeout=15)
        
        if tasks_resp.status_code == 200:
            tasks_data = tasks_resp.json()
            print(f"📡 Respuesta API: status={tasks_resp.status_code}, tareas_encontradas={len(tasks_data)}")
            print(f"📋 Tareas disponibles en caso {case_id}:")
            for i, task in enumerate(tasks_data):
                print(f"   {i+1}. {task.get('displayName')} (ID: {task.get('id')}, Estado: {task.get('state')})")

            # Filtrar por nombre exacto o que contenga el nombre buscado
            tareas_encontradas = []
            
            # Si no se especifica nombre de tarea, devolver todas
            if not task_name or task_name.strip() == "":
                tareas_encontradas = tasks_data
            else:
                for task in tasks_data:
                    task_display_name = task.get('displayName', '').lower()
                    task_internal_name = task.get('name', '').lower()
                    search_name = task_name.lower()
                    
                    if (search_name in task_display_name or 
                        search_name in task_internal_name or
                        task_display_name == search_name or
                        task_internal_name == search_name):
                        tareas_encontradas.append(task)
                    
            if task_name and task_name.strip():
                print(f"🎯 Tareas que coinciden con '{task_name}' ({len(tareas_encontradas)}):")
            else:
                print(f"📋 Todas las tareas disponibles ({len(tareas_encontradas)}):")
                
            for i, task in enumerate(tareas_encontradas):
                print(f"   {i+1}. ID: {task.get('id')}")
                print(f"       Nombre interno: '{task.get('name')}'")
                print(f"       Nombre display: '{task.get('displayName')}'")
                print(f"       Estado: {task.get('state')}")
                print(f"       Asignado a: {task.get('assigned_id', 'No asignado')}")
                if i < len(tareas_encontradas) - 1:
                    print(f"       ---")
                
            return tareas_encontradas
        else:
            print(f"⚠️ Error buscando tareas: {tasks_resp.status_code} - {tasks_resp.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error en búsqueda de tareas: {e}")
        return []

def obtener_contrato_tarea(task_id, cookies, headers):
    """
    Obtiene el contrato de una tarea para conocer qué datos necesita
    """
    print(f"📋 Obteniendo contrato para tarea {task_id}")
    
    try:
        contract_url = f"{url_bonita}/API/bpm/userTask/{task_id}/contract"
        contract_resp = requests.get(contract_url, cookies=cookies, headers=headers, timeout=15)
        
        if contract_resp.status_code == 200:
            contract_data = contract_resp.json()
            print(f"📄 Contrato de la tarea:")
            
            inputs = contract_data.get('inputs', [])
            print(f"   📥 Inputs requeridos ({len(inputs)}):")
            for input_item in inputs:
                input_name = input_item.get('name')
                input_type = input_item.get('type')
                input_description = input_item.get('description', 'N/A')
                print(f"      - {input_name} ({input_type}): {input_description}")
            
            constraints = contract_data.get('constraints', [])
            print(f"   ⚖️ Restricciones ({len(constraints)}):")
            for constraint in constraints:
                print(f"      - {constraint}")
                
            return contract_data
        else:
            print(f"⚠️ Error obteniendo contrato: {contract_resp.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error obteniendo contrato: {e}")
        return None

def ejecutar_tarea_bonita(task_id, task_data, cookies, headers, assign_to_current_user=True):
    """
    Ejecuta una tarea específica en Bonita con los datos proporcionados
    """
    print(f"🚀 Ejecutando tarea {task_id}")
    
    try:
        # URL para ejecutar la tarea
        execute_url = f"{url_bonita}/API/bpm/userTask/{task_id}/execution"
        
        # Parámetros para asignar la tarea al usuario actual si es necesario
        params = {}
        if assign_to_current_user:
            params['assign'] = 'true'
        
        print(f"📦 Datos a enviar a la tarea:")
        print(json.dumps(task_data, indent=2))
        
        # Ejecutar la tarea con los datos del contrato
        execute_resp = requests.post(
            execute_url, 
            json=task_data, 
            params=params,
            cookies=cookies, 
            headers=headers, 
            timeout=30
        )
        
        print(f"🎯 Respuesta ejecución tarea:")
        print(f"   Status Code: {execute_resp.status_code}")
        print(f"   Response Text: {execute_resp.text}")
        
        if execute_resp.status_code == 204:
            print("✅ Tarea ejecutada exitosamente")
            return True
        else:
            print(f"⚠️ Error ejecutando tarea: {execute_resp.status_code}")
            try:
                error_data = execute_resp.json()
                print(f"Error detalle: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando tarea: {e}")
        return False

def procesar_tarea_creacion_proyecto(case_id, proyecto, cookies, headers, request=None):
    """
    Busca y ejecuta la tarea 'Creación de Proyecto' con los datos del proyecto
    """
    print(f"🎯 === PROCESANDO TAREA CREACIÓN DE PROYECTO ===")
    
    # Posibles nombres de la tarea a buscar
    task_names = [
        'Creación de Proyecto',
        'Creacion de Proyecto', 
        'Create Project',
        'Crear Proyecto',
        'Creation Project'
    ]
    
    task_found = None
    
    # Buscar la tarea por diferentes nombres posibles
    for task_name in task_names:
        print(f"🔍 Buscando tarea: '{task_name}'")
        tareas = buscar_tarea_por_nombre(case_id, task_name, cookies, headers)
        
        if tareas:
            # Tomar la primera tarea que esté en estado 'ready' o 'assigned'
            for task in tareas:
                task_state = task.get('state', '').lower()
                if task_state in ['ready', 'assigned']:
                    task_found = task
                    print(f"✅ Tarea encontrada: {task.get('displayName')} (ID: {task.get('id')})")
                    break
        
        if task_found:
            break
    
    if not task_found:
        print("⚠️ No se encontró la tarea 'Creación de Proyecto'")
        return False
    
    task_id = task_found.get('id')
    
    # Obtener el contrato de la tarea para saber qué datos enviar
    contrato = obtener_contrato_tarea(task_id, cookies, headers)
    print(f"Este es el contrato de la tarea: {json.dumps(contrato, indent=2)}")
    
    # Preparar datos según el contrato específico de Bonita
    jwt_token = ""
    if request and hasattr(request, 'session'):
        jwt_token = request.session.get('jwt_token_render', '')
    
    # jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqYW4uZmlzaGVyQGNvcnJlby5jb20iLCJleHAiOjE3NjQxMDE1NDJ9.IP5W29Bd3irPWAUcCKqVGxtKu99GRqX0I-TN4q_N0A0"
    task_data = {
        # Objeto proyectoInput con los campos obligatorios según el contrato
        "proyectoInput": {
            "nombre": str(proyecto.nombre),
            "descripcion": str(proyecto.descripcion), 
            "estado": str(proyecto.estado),
            "originador": str(proyecto.originador.id)
        },
        
        # JWT Token de la sesión actual (campo obligatorio del contrato)
        "jwtTokenRender": jwt_token,
        
        # Nombre de la tarea (campo obligatorio del contrato)
        "nameTask": str(proyecto.nombre)
    }
    
    print(f"📦 Datos preparados para el contrato:")
    print(f"   - proyectoInput: {task_data['proyectoInput']}")
    print(f"   - jwtTokenRender: {'[SET]' if jwt_token else '[EMPTY]'}")
    print(f"   - nameTask: {task_data['nameTask']}")
    
    # Si hay etapas, incluirlas
    # if proyecto.etapas.exists():
    #     etapas_data = []
    #     for etapa in proyecto.etapas.all():
    #         etapas_data.append({
    #             "id": etapa.id,
    #             "nombre": etapa.nombre,
    #             "fechaInicio": etapa.fecha_inicio.isoformat() if etapa.fecha_inicio else None,
    #             "fechaFin": etapa.fecha_fin.isoformat() if etapa.fecha_fin else None
    #         })
    #     task_data["etapas"] = etapas_data

    
    # Ejecutar la tarea
    resultado = ejecutar_tarea_bonita(task_id, task_data, cookies, headers)
    
    if resultado:
        print("✅ Tarea 'Creación de Proyecto' ejecutada exitosamente")
        
        # VERIFICAR QUE LOS DATOS SE CARGARON CORRECTAMENTE
        print("🔍 Verificando que los datos se cargaron correctamente...")
        verificacion = verificar_datos_tarea_ejecutada(case_id, task_name, proyecto, cookies, headers)
        
        if verificacion:
            print(f"📊 Resumen de verificación:")
            print(f"   - Variables encontradas: {'✅' if verificacion['variables_found'] else '❌'}")
            print(f"   - BDM actualizado: {'✅' if verificacion['bdm_updated'] else '❌'}")
            print(f"   - Próximas tareas: {verificacion['next_tasks']}")
            print(f"   - Tareas completadas: {verificacion['completed_tasks']}")
        
    else:
        print("❌ Error al ejecutar tarea 'Creación de Proyecto'")
    
    print(f"🎯 === FIN PROCESAMIENTO TAREA ===")
    return resultado

def consultar_contexto_tarea(task_id, cookies, headers):
    """
    Consulta el contexto de una tarea específica para ver las variables disponibles
    """
    print(f"📋 Consultando contexto de tarea {task_id}")
    
    try:
        context_url = f"{url_bonita}/API/bpm/userTask/{task_id}/context"
        context_resp = requests.get(context_url, cookies=cookies, headers=headers, timeout=15)
        
        if context_resp.status_code == 200:
            context_data = context_resp.json()
            print(f"📄 Contexto de la tarea:")
            
            for key, value in context_data.items():
                print(f"   - {key}: {value}")
                
            return context_data
        else:
            print(f"⚠️ Error obteniendo contexto: {context_resp.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error consultando contexto: {e}")
        return None

def verificar_datos_tarea_ejecutada(case_id, task_name, proyecto, cookies, headers):
    """
    Verifica que los datos se cargaron correctamente después de ejecutar una tarea
    """
    print(f"🔍 === VERIFICANDO DATOS DE TAREA EJECUTADA ===")
    
    try:
        # 1. Verificar variables del proceso actualizadas
        print(f"📊 Verificando variables del proceso después de ejecutar '{task_name}':")
        
        variables_url = f"{url_bonita}/API/bpm/caseVariable"
        var_params = {
            'p': 0,
            'c': 50,
            'f': f'case_id={case_id}'
        }
        var_resp = requests.get(variables_url, params=var_params, cookies=cookies, headers=headers, timeout=15)
        
        if var_resp.status_code == 200:
            variables_data = var_resp.json()
            
            # Buscar variables relacionadas con el proyecto
            proyecto_vars = {}
            for var in variables_data:
                var_name = var.get('name', '').lower()
                if any(keyword in var_name for keyword in ['proyecto', 'project', 'name', 'task']):
                    proyecto_vars[var.get('name')] = var.get('value')
                    print(f"   ✅ {var.get('name')}: {var.get('value')}")
            
            # Verificar si tenemos las variables esperadas
            expected_vars = ['proyectoInput', 'nameTask', 'jwtTokenRender']
            found_vars = []
            
            for expected in expected_vars:
                if any(expected.lower() in key.lower() for key in proyecto_vars.keys()):
                    found_vars.append(expected)
            
            print(f"📋 Variables esperadas encontradas: {found_vars}")
            print(f"📋 Total variables del proyecto: {len(proyecto_vars)}")
            
        else:
            print(f"⚠️ Error obteniendo variables: {var_resp.status_code}")
        
        # 2. Verificar Business Data Model actualizado
        print(f"🏗️ Verificando BDM actualizado:")
        bdm_data = consultar_bdm_con_query_correcta(case_id, cookies, headers, proyecto.nombre)
        
        if bdm_data:
            print(f"✅ BDM actualizado correctamente")
            for obj in bdm_data:
                if obj.get('nombre') == proyecto.nombre:
                    print(f"   📊 Proyecto encontrado en BDM:")
                    print(f"      - ID: {obj.get('persistenceId')}")
                    print(f"      - Nombre: {obj.get('nombre')}")
                    print(f"      - Descripción: {obj.get('descripcion')}")
                    print(f"      - Estado: {obj.get('estado')}")
                    print(f"      - Originador: {obj.get('originador')}")
                    break
        else:
            print(f"⚠️ No se encontraron datos en BDM")
        
        # 3. Verificar estado de tareas después de la ejecución
        print(f"📋 Estado de tareas después de ejecutar '{task_name}':")
        tareas_actuales = listar_tareas_disponibles(case_id, cookies, headers)
        
        tareas_ready = [t for t in tareas_actuales if t.get('state') == 'ready']
        tareas_completed = [t for t in tareas_actuales if t.get('state') == 'completed']
        
        print(f"   📊 Tareas en estado 'ready': {len(tareas_ready)}")
        print(f"   ✅ Tareas completadas: {len(tareas_completed)}")
        
        for tarea in tareas_ready:
            print(f"      🟡 Próxima tarea: {tarea.get('displayName')} (ID: {tarea.get('id')})")
        
        return {
            'variables_found': len(proyecto_vars) > 0,
            'bdm_updated': len(bdm_data) > 0,
            'next_tasks': len(tareas_ready),
            'completed_tasks': len(tareas_completed)
        }
        
    except Exception as e:
        print(f"❌ Error verificando datos de tarea ejecutada: {e}")
        return None
    finally:
        print(f"🔍 === FIN VERIFICACIÓN DATOS TAREA ===")

def asignar_tarea_a_usuario(task_id, user_id, cookies, headers):
    """
    Asigna una tarea específica a un usuario antes de ejecutarla
    """
    print(f"👤 Asignando tarea {task_id} al usuario {user_id}")
    
    try:
        assign_url = f"{url_bonita}/API/bpm/humanTask/{task_id}"
        assign_data = {
            "assigned_id": str(user_id)
        }
        
        assign_resp = requests.put(assign_url, json=assign_data, cookies=cookies, headers=headers, timeout=15)
        
        if assign_resp.status_code == 200:
            print(f"✅ Tarea asignada exitosamente al usuario {user_id}")
            return True
        else:
            print(f"⚠️ Error asignando tarea: {assign_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error asignando tarea: {e}")
        return False

def listar_tareas_disponibles(case_id, cookies, headers):
    """
    Lista todas las tareas disponibles en un caso específico para debugging
    """
    print(f"📋 === LISTANDO TODAS LAS TAREAS DEL CASO {case_id} ===")
    
    try:
        tasks_url = f"{url_bonita}/API/bpm/humanTask"
        tasks_params = {
            'p': 0,
            'c': 100,
            'f': f'caseId={case_id}'
        }
        
        tasks_resp = requests.get(tasks_url, params=tasks_params, cookies=cookies, headers=headers, timeout=15)
        
        if tasks_resp.status_code == 200:
            tasks_data = tasks_resp.json()
            
            print(f"📋 Total de tareas encontradas: {len(tasks_data)}")
            for i, task in enumerate(tasks_data, 1):
                print(f"   [{i}] Tarea:")
                print(f"       ID: {task.get('id')}")
                print(f"       Nombre: {task.get('name')}")
                print(f"       Display Name: {task.get('displayName')}")
                print(f"       Estado: {task.get('state')}")
                print(f"       Tipo: {task.get('type')}")
                print(f"       Asignado a: {task.get('assigned_id', 'No asignado')}")
                print(f"       Fecha de actualización: {task.get('last_update_date')}")
                print("       ---")
                
            return tasks_data
        else:
            print(f"⚠️ Error listando tareas: {tasks_resp.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error listando tareas: {e}")
        return []

def cargar_etapas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == "POST":
        form = EtapaForm(request.POST)
        if form.is_valid():
            form.save(proyecto=proyecto.id)

            if request.POST.get("action") == "agregar":
                return redirect('cargar_etapas', proyecto_id=proyecto.id)

            elif request.POST.get("action") == "guardar":


                print(f"TRAER PROCESO")

                url_get_process = f"{url_bonita}/API/bpm/process"
                # Parámetros correctos según la documentación de Bonita API
                params = {
                    'p': 0,  # índice de página (requerido)
                    'c': 20,  # cantidad máxima de elementos (requerido)
                    'f': 'name=Ciclo de vida de proyecto'  # filtro por nombre
                }
                cookies = request.session.get("cookies")
                headers = request.session.get("headers")
                resp = requests.get(url_get_process, params=params, cookies=cookies, headers=headers, timeout=30)

                print(f"RESPUESTA OBTENER PROCESO: {resp.status_code}")
                print(f"RESPUESTA OBTENER PROCESO TEXTO: {resp.text}")
                
                if resp.status_code == 200:
                    processes = resp.json()
                    if processes:
                        # Tomar el primer proceso que coincida
                        proceso_bonita = processes[0]
                        process_definition_id = proceso_bonita['id']
                        print(f"ID del proceso encontrado: {process_definition_id}")
                        # Actualizar el process_id en la sesión si es necesario
                        request.session['process_id_ciclo_vida'] = process_definition_id
                    else:
                        print(f"⚠️ No se encontró el proceso 'Creacion de Proyecto' {resp.text}")
                else:
                    print(f"❌ Error al obtener proceso: {resp.text}")

                # Construir el payload según el contrato de Bonita y el BDM
                # Según tu BDM, BusinessObject tiene: nombre, descripcion, estado, originador
                
                payload = {
                    # Variables booleanas del proceso
                    "cubierto": True,  # boolean
                    "entregados": True,  # boolean
                    
                    # HashMap simple para datos adicionales si es necesario
                    "proyectoInput": {
                        "id": proyecto.id,
                        "nombre": proyecto.nombre,
                        "descripcion": proyecto.descripcion
                    },

                    "jwtTokenRender": request.session.get('jwt_token_render'),

                    # Objeto de negocio (BDM) - debe coincidir exactamente con tu BusinessObject
                    "proyectoBDMInput": {
                        "nombre": str(proyecto.nombre),           
                        "descripcion": str(proyecto.descripcion), 
                        "estado": str(proyecto.estado),       
                        "originador": str(proyecto.originador.id)  # String según BDM
                    },
                    "proyectoBDMInpInput": {
                        "nombre": str(proyecto.nombre),           
                        "descripcion": str(proyecto.descripcion), 
                        "estado": str(proyecto.estado),       
                        "originador": str(proyecto.originador.id)  # String según BDM
                    },
                    "proyectoBDMInpInput1": {
                        "nombre": str(proyecto.nombre),           
                        "descripcion": str(proyecto.descripcion), 
                        "estado": str(proyecto.estado),       
                        "originador": str(proyecto.originador.id)  # String según BDM
                    },
                    "proyectoInput": {
                        "nombre": str(proyecto.nombre),           
                        "descripcion": str(proyecto.descripcion), 
                        "estado": str(proyecto.estado),       
                        "originador": str(proyecto.originador.id)  # String según BDM
                    },
                    "proyectoInput1": {
                        "nombre": str(proyecto.nombre),           
                        "descripcion": str(proyecto.descripcion), 
                        "estado": str(proyecto.estado),       
                        "originador": str(proyecto.originador.id)  # String según BDM
                    },
                    "name": str(proyecto.nombre),  
                }

                try:
                    cookies = request.session.get("cookies")
                    headers = request.session.get("headers")
                    print(f"📋 Session items: {dict(request.session.items())}")
                    process_obs_id = request.session.get("process_id_ciclo_observacion")
                    process_id = request.session.get("process_id_ciclo_vida")
                    
                    print(f"🔍 Datos de sesión Bonita:")
                    print(f"   - Cookies: {bool(cookies)}")
                    print(f"   - Headers: {bool(headers)}")
                    print(f"   - Process ID Ciclo Vida: {process_id}")
                    print(f"   - Process ID Ciclo Observación: {process_obs_id}")

                    if not cookies or not headers or not process_id:
                        raise Exception("Faltan datos de sesión Bonita")
                    
                    # Validar que el process_id sea un número válido
                    try:
                        process_id = str(process_id).strip()
                        if not process_id.isdigit():
                            raise Exception(f"Process ID inválido: {process_id}")
                    except (ValueError, AttributeError):
                        raise Exception("Process ID debe ser numérico")

                    start_url = f"{url_bonita}/API/bpm/process/{process_id}/instantiation"
                    # payload = {
                    #     "nombre" : str(proyecto.nombre)
                    # }

                    # start_url = f"{url_bonita}/API/bpm/process/{process_obs_id}/instantiation"
                    
                    print("📦 Payload a Bonita:")
                    print(json.dumps(payload, indent=2))
                    print(f"🔗 URL: {start_url}")
                    print(f"🆔 Process ID: {process_id}")
                    
                    # Validaciones según el contrato de Bonita
                    if not proyecto.nombre or not proyecto.descripcion:
                        raise Exception("Faltan datos del proyecto (nombre o descripción)")
                    
                    if not proyecto.etapas.exists():
                        raise Exception("El proyecto debe tener al menos una etapa")
                    
                    # Validar que el originador exista
                    if not proyecto.originador or not proyecto.originador.id:
                        raise Exception("El proyecto debe tener un originador válido")
                    
                    # Validar que todas las etapas tengan ID válido
                    for etapa in proyecto.etapas.all():
                        if not etapa.id:
                            raise Exception(f"La etapa '{etapa}' no tiene ID válido")
                        if not etapa.nombre or not etapa.fecha_inicio:
                            raise Exception(f"La etapa '{etapa}' tiene datos incompletos")

                    resp = requests.post(start_url, json=payload, cookies=cookies, headers=headers, timeout=30)

                    print(f"🔥 Status Code: {resp.status_code}")
                    print(f"📋 Response Headers: {dict(resp.headers)}")
                    print(f"📄 Response Text: {resp.text}")

                    if resp.status_code == 200 or resp.status_code == 201:
                        response_data = resp.json()
                        print("✅ Proyecto completo enviado a Bonita:", json.dumps(response_data, indent=2))
                        
                        # Guardar el case ID para futuras operaciones
                        if 'caseId' in response_data:
                            case_id = response_data['caseId']
                            print(f"🆔 Case ID generado: {case_id}")
                            
                            # Guardar en la sesión para uso posterior
                            request.session['bonita_case_id'] = case_id
                            
                            # Aquí puedes guardar el case_id en tu modelo si lo necesitas
                            # proyecto.case_id_bonita = case_id
                            # proyecto.save()
                            
                            # VERIFICAR QUE LOS DATOS SE GUARDARON EN BONITA
                            verificar_datos_bonita(case_id, cookies, headers, proyecto.nombre)
                            
                            # LISTAR TODAS LAS TAREAS DISPONIBLES PARA DEBUG
                            listar_tareas_disponibles(case_id, cookies, headers)
                            
                            # BUSCAR Y EJECUTAR LA TAREA 'CREACIÓN DE PROYECTO'
                            print("🎯 Iniciando procesamiento de tarea 'Creación de Proyecto'")
                            tarea_ejecutada = procesar_tarea_creacion_proyecto(case_id, proyecto, cookies, headers, request)
                            
                            if tarea_ejecutada:
                                print("✅ Flujo completo: Proceso iniciado y tarea ejecutada")
                            else:
                                print("⚠️ Proceso iniciado, pero error en ejecución de tarea")
                                
                        print("🎯 Verificación de datos completada")
                    else:
                        error_msg = f"Error al enviar a Bonita (Status: {resp.status_code})"
                        print(f"⚠️ {error_msg}")
                        print(f"Response Text: {resp.text}")
                        try:
                            error_json = resp.json()
                            print(f"Error JSON: {json.dumps(error_json, indent=2)}")
                            if 'message' in error_json:
                                error_msg = f"Bonita Error: {error_json['message']}"
                            if 'cause' in error_json:
                                print(f"Causa: {error_json['cause']}")
                        except:
                            pass
                        raise Exception(f"Error de Bonita: {error_msg}")

                except requests.exceptions.RequestException as e:
                    print(f"❌ Error de conexión con Bonita: {e}")
                except Exception as e:
                    print(f"❌ Error general al sincronizar con Bonita: {e}")

                return redirect('detalle_proyecto', pk=proyecto.id)

    else:
        form = EtapaForm()

    return render(request, 'cargar_etapa.html', {
        'form': form,
        'proyecto': proyecto,
    })

def consultar_datos_bonita(request):
    """
    Vista para consultar manualmente los datos almacenados en Bonita
    """
    if request.method == "POST":
        case_id = request.POST.get('case_id') or request.session.get('bonita_case_id')
        
        if case_id:
            cookies = request.session.get("cookies")
            headers = request.session.get("headers")
            
            if cookies and headers:
                verificar_datos_bonita(case_id, cookies, headers)
                return render(request, 'consultar_bonita.html', {
                    'success': True,
                    'case_id': case_id,
                    'message': 'Consulta realizada. Revisa los logs para ver los resultados.'
                })
            else:
                return render(request, 'consultar_bonita.html', {
                    'error': 'No hay sesión activa con Bonita'
                })
        else:
            return render(request, 'consultar_bonita.html', {
                'error': 'No se proporcionó Case ID'
            })
    
    # GET request - mostrar formulario
    current_case_id = request.session.get('bonita_case_id')
    return render(request, 'consultar_bonita.html', {
        'current_case_id': current_case_id
    })

def obtener_todos_los_procesos_bonita(request):
    """
    Vista para obtener todos los procesos activos en Bonita
    """
    try:
        cookies = request.session.get("cookies")
        headers = request.session.get("headers")
        
        if not cookies or not headers:
            return render(request, 'procesos_bonita.html', {
                'error': 'No hay sesión activa con Bonita'
            })
        
        # Obtener todos los casos/procesos
        cases_url = f"{url_bonita}/API/bpm/case"
        cases_params = {'p': 0, 'c': 50, 'o': 'start DESC'}  # Ordenar por fecha de inicio
        
        cases_resp = requests.get(cases_url, params=cases_params, cookies=cookies, headers=headers, timeout=15)
        
        if cases_resp.status_code == 200:
            cases_data = cases_resp.json()
            
            # Para cada caso, obtener sus variables
            procesos_con_datos = []
            for case in cases_data:
                case_id = case.get('id')
                
                # Obtener variables del caso usando el endpoint correcto
                var_url = f"{url_bonita}/API/bpm/caseVariable"
                var_params = {
                    'p': 0,
                    'c': 20,
                    'f': f'case_id={case_id}'
                }
                var_resp = requests.get(var_url, params=var_params, cookies=cookies, headers=headers, timeout=10)
                
                variables = []
                if var_resp.status_code == 200:
                    variables = var_resp.json()
                
                procesos_con_datos.append({
                    'case': case,
                    'variables': variables
                })
            
            return render(request, 'procesos_bonita.html', {
                'procesos': procesos_con_datos,
                'total': len(procesos_con_datos)
            })
        else:
            return render(request, 'procesos_bonita.html', {
                'error': f'Error consultando procesos: {cases_resp.status_code}'
            })
            
    except Exception as e:
        return render(request, 'procesos_bonita.html', {
            'error': f'Error: {str(e)}'
        })

def obtener_variable_especifica_bonita(case_id, variable_name, cookies, headers):
    """
    Función para obtener una variable específica usando el formato correcto [case_id,name]
    """
    try:
        # Según la documentación: /API/bpm/caseVariable/{case_id}/{variable_name}
        var_url = f"{url_bonita}/API/bpm/caseVariable/{case_id}/{variable_name}"
        resp = requests.get(var_url, cookies=cookies, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            var_data = resp.json()
            print(f"📋 Variable '{variable_name}':")
            print(f"   - Valor: {var_data.get('value')}")
            print(f"   - Tipo: {var_data.get('type')}")
            print(f"   - Descripción: {var_data.get('description', 'N/A')}")
            return var_data
        else:
            print(f"⚠️ Variable '{variable_name}' no encontrada: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error obteniendo variable '{variable_name}': {e}")
        return None

def obtener_queries_bdm_disponibles(cookies, headers, business_data_type="com.company.model.BusinessObject"):
    """
    Función para obtener las queries disponibles en el BDM
    """
    try:
        # Consultar queries disponibles para el BusinessObject
        queries_url = f"{url_bonita}/API/bdm/businessDataQuery/{business_data_type}"
        queries_resp = requests.get(queries_url, cookies=cookies, headers=headers, timeout=10)
        
        if queries_resp.status_code == 200:
            queries_data = queries_resp.json()
            print(f"📋 Queries disponibles para {business_data_type}:")
            for query in queries_data:
                print(f"   - {query.get('name')}: {query.get('returnType')}")
                if query.get('queryParameters'):
                    params = [p.get('name') for p in query.get('queryParameters', [])]
                    print(f"     Parámetros: {', '.join(params)}")
            return queries_data
        else:
            print(f"⚠️ Error obteniendo queries BDM: {queries_resp.status_code} - {queries_resp.text}")
            return []
    except Exception as e:
        print(f"❌ Error consultando queries BDM: {e}")
        return []

def consultar_bdm_con_query_correcta(case_id, cookies, headers, proyecto_nombre=None):
    """
    Función mejorada para consultar BDM con la query correcta
    """
    print("🏗️ Consultando Business Data Model...")
    
    # Primero obtener las queries disponibles
    queries_disponibles = obtener_queries_bdm_disponibles(cookies, headers)
    
    # Lista de queries comunes para intentar
    queries_para_probar = ['find', 'findAll', 'findById']
    
    # Si tenemos nombre de proyecto, agregar queries de búsqueda por nombre
    if proyecto_nombre:
        queries_para_probar.extend(['findByNombre', 'findByName'])
    
    bdm_url = f"{url_bonita}/API/bdm/businessData/com.company.model.BusinessObject"
    
    for query_name in queries_para_probar:
        try:
            print(f"🔍 Probando query: {query_name}")
            
            if query_name in ['findByNombre', 'findByName'] and proyecto_nombre:
                # Query con parámetro de nombre
                params = {
                    'q': query_name,
                    'p': 0,
                    'c': 20,
                    'nombre': proyecto_nombre
                }
            else:
                # Query simple
                params = {
                    'q': query_name,
                    'p': 0,
                    'c': 20
                }
            
            resp = requests.get(bdm_url, params=params, cookies=cookies, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                bdm_data = resp.json()
                print(f"✅ Query '{query_name}' exitosa - Objetos encontrados: {len(bdm_data)}")
                
                for i, obj in enumerate(bdm_data):
                    # Filtrar manualmente si es necesario
                    if proyecto_nombre and obj.get('nombre') != proyecto_nombre:
                        continue
                        
                    print(f"   [{i+1}] ID: {obj.get('persistenceId')}")
                    print(f"       Nombre: {obj.get('nombre')}")
                    print(f"       Descripción: {obj.get('descripcion')}")
                    print(f"       Estado: {obj.get('estado')}")
                    print(f"       Originador: {obj.get('originador')}")
                    print("       ---")
                
                return bdm_data  # Retornar datos si fue exitoso
                
            else:
                print(f"⚠️ Query '{query_name}' falló: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ Error con query '{query_name}': {e}")
            continue
    
        print("❌ Ninguna query BDM funcionó")
    return []

def ejecutar_tarea_manual(request):
    """
    Vista para ejecutar manualmente una tarea específica (útil para testing)
    """
    if request.method == "POST":
        case_id = request.POST.get('case_id') or request.session.get('bonita_case_id')
        task_name = request.POST.get('task_name', 'Creación de Proyecto')
        
        if case_id:
            cookies = request.session.get("cookies")
            headers = request.session.get("headers")
            
            if cookies and headers:
                # Buscar el proyecto asociado al case_id si existe
                proyecto = None
                proyecto_id = request.POST.get('proyecto_id')
                if proyecto_id:
                    try:
                        proyecto = Proyecto.objects.get(id=proyecto_id)
                    except Proyecto.DoesNotExist:
                        pass
                
                # Listar tareas disponibles
                tareas_disponibles = listar_tareas_disponibles(case_id, cookies, headers)
                
                # Intentar ejecutar la tarea específica si se proporcionó un proyecto
                resultado = False
                if proyecto and task_name:
                    resultado = procesar_tarea_creacion_proyecto(case_id, proyecto, cookies, headers, request)
                
                return render(request, 'ejecutar_tarea.html', {
                    'success': True,
                    'case_id': case_id,
                    'task_name': task_name,
                    'resultado': resultado,
                    'tareas_disponibles': tareas_disponibles,
                    'message': f'Ejecución de tarea completada. Resultado: {"Exitoso" if resultado else "Error"}.'
                })
            else:
                return render(request, 'ejecutar_tarea.html', {
                    'error': 'No hay sesión activa con Bonita'
                })
        else:
            return render(request, 'ejecutar_tarea.html', {
                'error': 'No se proporcionó Case ID'
            })
    
    # GET request - mostrar formulario
    current_case_id = request.session.get('bonita_case_id')
    proyectos = Proyecto.objects.all()
    return render(request, 'ejecutar_tarea.html', {
        'current_case_id': current_case_id,
        'proyectos': proyectos
    })

def verificar_tarea_ejecutada(request):
    """
    Vista para verificar manualmente los datos de una tarea ejecutada
    """
    if request.method == "POST":
        case_id = request.POST.get('case_id') or request.session.get('bonita_case_id')
        task_name = request.POST.get('task_name', 'Creación de Proyecto')
        
        if case_id:
            cookies = request.session.get("cookies")
            headers = request.session.get("headers")
            
            if cookies and headers:
                # Buscar el proyecto asociado si existe
                proyecto = None
                proyecto_id = request.POST.get('proyecto_id')
                if proyecto_id:
                    try:
                        proyecto = Proyecto.objects.get(id=proyecto_id)
                    except Proyecto.DoesNotExist:
                        pass
                
                # Realizar verificación completa
                if proyecto:
                    verificacion = verificar_datos_tarea_ejecutada(case_id, task_name, proyecto, cookies, headers)
                else:
                    # Verificación básica sin proyecto específico
                    verificacion = {
                        'variables_found': False,
                        'bdm_updated': False,
                        'next_tasks': 0,
                        'completed_tasks': 0
                    }
                
                # Listar tareas disponibles
                tareas_disponibles = listar_tareas_disponibles(case_id, cookies, headers)
                
                # Obtener variables del proceso
                variables_proceso = {}
                try:
                    variables_url = f"{url_bonita}/API/bpm/caseVariable"
                    var_params = {
                        'p': 0,
                        'c': 50,
                        'f': f'case_id={case_id}'
                    }
                    var_resp = requests.get(variables_url, params=var_params, cookies=cookies, headers=headers, timeout=15)
                    
                    if var_resp.status_code == 200:
                        variables_data = var_resp.json()
                        for var in variables_data:
                            variables_proceso[var.get('name')] = var.get('value')
                except:
                    pass
                
                return render(request, 'verificar_tarea.html', {
                    'success': True,
                    'case_id': case_id,
                    'task_name': task_name,
                    'proyecto': proyecto,
                    'verificacion': verificacion,
                    'tareas_disponibles': tareas_disponibles,
                    'variables_proceso': variables_proceso,
                    'message': 'Verificación realizada. Revisa los resultados detallados.'
                })
            else:
                return render(request, 'verificar_tarea.html', {
                    'error': 'No hay sesión activa con Bonita'
                })
        else:
            return render(request, 'verificar_tarea.html', {
                'error': 'No se proporcionó Case ID'
            })
    
    # GET request - mostrar formulario
    current_case_id = request.session.get('bonita_case_id')
    proyectos = Proyecto.objects.all()
    return render(request, 'verificar_tarea.html', {
        'current_case_id': current_case_id,
        'proyectos': proyectos
    })

def diagnosticar_proceso_bonita(case_id, cookies, headers):
    """
    Función de diagnóstico completo para un proceso de Bonita
    """
    print("🔧 === DIAGNÓSTICO COMPLETO DEL PROCESO ===")
    
    try:
        # 1. Verificar información del caso
        process_url = f"{url_bonita}/API/bpm/case/{case_id}"
        proc_resp = requests.get(process_url, cookies=cookies, headers=headers, timeout=15)
        
        if proc_resp.status_code == 200:
            proc_data = proc_resp.json()
            print(f"✅ Información del caso {case_id}:")
            print(f"   - Estado: {proc_data.get('state')}")
            print(f"   - Proceso: {proc_data.get('processDefinitionId')}")
            print(f"   - Iniciado: {proc_data.get('start')}")
            print(f"   - Versión: {proc_data.get('version')}")
        else:
            print(f"❌ Error obteniendo información del caso: {proc_resp.status_code}")
        
        # 2. Listar TODAS las tareas (humanas y automáticas)
        tasks_url = f"{url_bonita}/API/bpm/humanTask"
        tasks_params = {'p': 0, 'c': 100, 'f': f'caseId={case_id}'}
        tasks_resp = requests.get(tasks_url, params=tasks_params, cookies=cookies, headers=headers, timeout=15)
        
        print(f"\n📋 Tareas humanas disponibles:")
        if tasks_resp.status_code == 200:
            human_tasks = tasks_resp.json()
            if human_tasks:
                for i, task in enumerate(human_tasks):
                    print(f"   {i+1}. '{task.get('displayName')}' (ID: {task.get('id')})")
                    print(f"      - Nombre interno: '{task.get('name')}'")
                    print(f"      - Estado: {task.get('state')}")
                    print(f"      - Tipo: {task.get('type')}")
                    print(f"      - Asignada a: {task.get('assigned_id', 'No asignada')}")
            else:
                print("   ⚠️ No hay tareas humanas disponibles")
        else:
            print(f"   ❌ Error obteniendo tareas humanas: {tasks_resp.status_code}")
        
        # 3. Verificar tareas automáticas/actividades
        activities_url = f"{url_bonita}/API/bpm/activity"
        activities_params = {'p': 0, 'c': 100, 'f': f'caseId={case_id}'}
        activities_resp = requests.get(activities_url, params=activities_params, cookies=cookies, headers=headers, timeout=15)
        
        print(f"\n🤖 Actividades/Tareas automáticas:")
        if activities_resp.status_code == 200:
            activities = activities_resp.json()
            if activities:
                for i, activity in enumerate(activities):
                    print(f"   {i+1}. '{activity.get('displayName')}' (ID: {activity.get('id')})")
                    print(f"      - Nombre: '{activity.get('name')}'")
                    print(f"      - Estado: {activity.get('state')}")
                    print(f"      - Tipo: {activity.get('type')}")
            else:
                print("   ℹ️ No hay actividades automáticas")
        else:
            print(f"   ❌ Error obteniendo actividades: {activities_resp.status_code}")
        
        # 4. Verificar variables del proceso
        variables_url = f"{url_bonita}/API/bpm/caseVariable"
        var_params = {'p': 0, 'c': 20, 'f': f'case_id={case_id}'}
        var_resp = requests.get(variables_url, params=var_params, cookies=cookies, headers=headers, timeout=15)
        
        print(f"\n📊 Variables del proceso:")
        if var_resp.status_code == 200:
            variables = var_resp.json()
            if variables:
                for var in variables:
                    print(f"   - {var.get('name')}: {var.get('value')}")
            else:
                print("   ℹ️ No hay variables definidas")
        else:
            print(f"   ❌ Error obteniendo variables: {var_resp.status_code}")
            
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
    
    print("🔧 === FIN DIAGNÓSTICO ===\n")