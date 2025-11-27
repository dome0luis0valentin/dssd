import os
import django
import sys
from datetime import date

# === Inicializar Django ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dssd.settings')
django.setup()

# === Imports de modelos ===
from ONG.models import ONG
from user.models import User
from BoardOfDirectors.models import ConsejoDirectivo
from Project.models import Proyecto
from TypeCoverage.models import TipoCobertura
from CoverageRequest.models import PedidoCobertura
from Stage.models import Etapa
from Observation.models import Observacion  # si tu app se llama distinto, decime


# ============================
# BORRAR DATOS ANTERIORES
# ============================
Observacion.objects.all().delete()
Etapa.objects.all().delete()
PedidoCobertura.objects.all().delete()
Proyecto.objects.all().delete()
TipoCobertura.objects.all().delete()
ONG.objects.all().delete()
User.objects.all().delete()
ConsejoDirectivo.objects.all().delete()

print("Datos anteriores eliminados.")


# ============================
# CREAR ONGs + USUARIOS
# ============================
usuarios_ong = [
    ("Isabel", "Bissale", "isabel.bissale"),
    ("Jan", "Fisher", "jan.fisher"),
    ("Patrick", "Gardenier", "patrick.gardenier"),
    ("Thorsten", "Hartmann", "thorsten.hartmann"),
    ("Joseph", "Hovell", "joseph.hovell"),
    ("William", "Jobs", "william.jobs"),
    ("Virginie", "Jomphe", "virginie.jomphe"),
    ("Helen", "Kelly", "helen.kelly"),
    ("Carlos", "Mendez", "carlos.mendez"),
    ("Lucia", "Ramirez", "lucia.ramirez")
]

ong_objects = []

for i in range(5):
    ong = ONG.objects.create(nombre=f"ONG{i+1}")
    ong_objects.append(ong)

    for j in range(2):
        idx = i * 2 + j
        nombre, apellido, username = usuarios_ong[idx]

        user = User.objects.create(
            nombre=nombre,
            apellido=apellido,
            edad=25 + idx,
            email=f"{username}@correo.com",
            username=username,
            ong=ong
        )
        user.set_password("admin")
        user.save()

    print(f"ONG creada: {ong.nombre}")

# ============================
# CONSEJO DIRECTIVO
# ============================
consejo = ConsejoDirectivo.objects.create(nombre="Consejo Directivo Principal")

miembros_cd = [
    ("Walter", "Bates", "walter.bates"),
    ("Daniela", "Angelo", "daniela.angelo"),
    ("Giovanna", "Almeida", "giovanna.almeida")
]

for i, (nombre, apellido, username) in enumerate(miembros_cd):
    u = User.objects.create(
        nombre=nombre,
        apellido=apellido,
        edad=35 + i,
        email=f"{username}@consejo.com",
        username=username,
        consejo=consejo
    )
    u.set_password("admin")
    u.save()

print("Consejo Directivo creado.")


# ============================
# TIPOS DE COBERTURA
# ============================
tipo1 = TipoCobertura.objects.create(nombre="Salud")
tipo2 = TipoCobertura.objects.create(nombre="Educación")

print("Tipos de cobertura creados.")


# ============================
# PROYECTOS
# ============================
ong1, ong2 = ong_objects[0], ong_objects[1]

proy1 = Proyecto.objects.create(
    nombre="Proyecto Agua Limpia",
    descripcion="Brindar acceso a agua potable",
    estado="proceso",
    originador=ong1
)

proy2 = Proyecto.objects.create(
    nombre="Proyecto Escuelas Verdes",
    descripcion="Mejorar la infraestructura escolar",
    estado="ejecucion",
    originador=ong2
)

print("Proyectos creados.")


# ============================
# PEDIDOS DE COBERTURA
# ============================
pedido1 = PedidoCobertura.objects.create(
    estado=False,
    tipo_cobertura=tipo1
)

pedido2 = PedidoCobertura.objects.create(
    estado=True,
    tipo_cobertura=tipo2
)

print("Pedidos de cobertura creados.")


# ============================
# ETAPAS
# ============================
Etapa.objects.create(
    proyecto=proy1,
    nombre="Diagnóstico",
    descripcion="Evaluación de necesidades",
    fecha_inicio=date(2025, 1, 10),
    pedido=pedido1
)

Etapa.objects.create(
    proyecto=proy2,
    nombre="Ejecución",
    descripcion="Implementación de actividades",
    fecha_inicio=date(2025, 2, 15),
    pedido=pedido2
)

print("Etapas creadas.")


# ============================
# OBSERVACIONES
# ============================
Observacion.objects.create(
    descripcion="Buen progreso inicial",
    proyecto=proy1,
    consejo=consejo
)

Observacion.objects.create(
    descripcion="Requiere más voluntarios",
    proyecto=proy2,
    consejo=consejo
)

print("Observaciones creadas.")
print("✅ Datos iniciales cargados correctamente.")
