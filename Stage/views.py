from django.shortcuts import render, redirect, get_object_or_404
from .models import Etapa
from .forms import EtapaForm
from Project.models import Proyecto
from CoverageRequest.models import PedidoCobertura
url_bonita = "http://localhost:8080/bonita"
import requests

def cargar_etapas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == "POST":
        form = EtapaForm(request.POST)
        if form.is_valid():
            form.save(proyecto=proyecto.id)

            # Diferenciamos según el botón presionado
            if request.POST.get("action") == "agregar":
                # Redirigir a la misma página para agregar otra etapa
                return redirect('cargar_etapas', proyecto_id=proyecto.id)
            elif request.POST.get("action") == "guardar":
                # 🔹 Armar payload completo
                etapas = proyecto.etapas.all()
                etapas_payload = []

                for etapa in etapas:
                    pedido = etapa.pedido
                    tipo_cobertura = pedido.tipo_cobertura if pedido else None

                    etapas_payload.append({
                        "nombre": etapa.nombre,
                        "descripcion": etapa.descripcion,
                        "fecha_inicio": etapa.fecha_inicio.strftime("%Y-%m-%d"),
                        "fecha_fin": etapa.fecha_fin.strftime("%Y-%m-%d") if etapa.fecha_fin else None,
                        "pedido": {
                            "estado": pedido.estado if pedido else None,
                            "tipo_cobertura": tipo_cobertura.nombre if tipo_cobertura else None
                        }
                    })

                payload = {
                    "proyectoInput": {
                        "nombre": proyecto.nombre,
                        "descripcion": proyecto.descripcion,
                        "estado": proyecto.estado,
                        "originador": proyecto.originador.nombre,
                        "etapas": etapas_payload
                    }
                }

                # 🔹 Enviar a Bonita
                try:
                    cookies = request.session.get("cookies")
                    headers = request.session.get("headers")
                    process_id = request.session.get("process_id_ciclo_vida")

                    if not cookies or not headers or not process_id:
                        raise Exception("Faltan datos de sesión Bonita")

                    start_url = f"{url_bonita}/API/bpm/process/{process_id}/instantiation"
                    resp = requests.post(start_url, json=payload, cookies=cookies, headers=headers)

                    if resp.status_code == 200:
                        print("✅ Proyecto completo enviado a Bonita:", resp.json())
                    else:
                        print("⚠️ Error al enviar a Bonita:", resp.text)

                except Exception as e:
                    print("❌ Error al sincronizar con Bonita:", e)

                return redirect('detalle_proyecto', pk=proyecto.id)
    else:
        form = EtapaForm()

    return render(request, 'cargar_etapa.html', {
        'form': form,
        'proyecto': proyecto,
    })

