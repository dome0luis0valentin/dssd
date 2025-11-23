from django.shortcuts import render, redirect, get_object_or_404
from .models import Etapa
from .forms import EtapaForm
from Project.models import Proyecto
import json
import requests

url_bonita = "http://localhost:8080/bonita"

def cargar_etapas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == "POST":
        form = EtapaForm(request.POST)
        if form.is_valid():
            form.save(proyecto=proyecto.id)

            if request.POST.get("action") == "agregar":
                return redirect('cargar_etapas', proyecto_id=proyecto.id)

            elif request.POST.get("action") == "guardar":

                # SOLO persistenceId_string (lo único permitido por el contrato)
                etapas_payload = [
                    {"persistenceId_string": str(etapa.id)}
                    for etapa in proyecto.etapas.all()
                ]

                payload = {
                    "proyectoBDMInput": {
                        "nombre": proyecto.nombre,
                        "descripcion": proyecto.descripcion,
                        "estado": proyecto.estado,
                        "originador": proyecto.originador.id,
                        "etapas": etapas_payload
                    }
                }

                try:
                    cookies = request.session.get("cookies")
                    headers = request.session.get("headers")
                    process_id = request.session.get("process_id_ciclo_vida")

                    if not cookies or not headers or not process_id:
                        raise Exception("Faltan datos de sesión Bonita")

                    start_url = f"{url_bonita}/API/bpm/process/{process_id}/instantiation"
                    resp = requests.post(start_url, json=payload, cookies=cookies, headers=headers)

                    print("📦 Payload a Bonita:")
                    print(json.dumps(payload, indent=2))

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
