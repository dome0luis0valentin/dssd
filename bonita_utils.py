import requests

url_bonita = "http://localhost:8080/bonita"

def load_process_ids(request):
    cookies = request.session.get("cookies", {})
    headers = request.session.get("headers", {})

    if not cookies or not headers:
        print("⚠️ No hay sesión Bonita, no se pueden cargar procesos.")
        return

    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)

    try:
        # Ciclo de Vida
        resp = session.get(
            f"{url_bonita}/API/bpm/process",
            params={"f": "name=Ciclo de Vida de Proyecto"},
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200 and resp.json():
            request.session["process_id_ciclo_vida"] = resp.json()[0]["id"]

        # Ciclo Observaciones
        resp2 = session.get(
            f"{url_bonita}/API/bpm/process",
            params={"f": "name=Ciclo de Observaciones"},
            headers=headers,
            timeout=10
        )
        if resp2.status_code == 200 and resp2.json():
            request.session["process_id_ciclo_observacion"] = resp2.json()[0]["id"]

    except Exception as e:
        print("❌ Error cargando procesos:", e)
