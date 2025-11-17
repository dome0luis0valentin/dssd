import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dssd.settings')
django.setup()

from ONG.models import ONG
from user.models import User
from BoardOfDirectors.models import ConsejoDirectivo

# --- BORRAR DATOS EXISTENTES ---
ONG.objects.all().delete()
User.objects.all().delete()
ConsejoDirectivo.objects.all().delete()
print("Datos anteriores eliminados.")

# --- CREAR 5 ONGs con 2 usuarios cada una ---
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

for i in range(5):
    ong = ONG.objects.create(nombre=f"ONG{i+1}")
    for j in range(2):
        idx = i * 2 + j
        nombre, apellido, username = usuarios_ong[idx]
        usuario = User.objects.create(
            nombre=nombre,
            apellido=apellido,
            edad=28 + idx,
            email=f"{username}@correo.com",
            username=username,
            ong=ong
        )
        usuario.set_password("admin")
        usuario.save()
    print(f"ONG creada: {ong.nombre} con usuarios {usuarios_ong[i*2][0]} y {usuarios_ong[i*2+1][0]}")

# --- CREAR Consejo Directivo con 3 usuarios únicos ---
consejo = ConsejoDirectivo.objects.create(nombre="Consejo Directivo Principal")

miembros_cd = [
    ("Walter", "Bates", "walter.bates"),
    ("Daniela", "Angelo", "daniela.angelo"),
    ("Giovanna", "Almeida", "giovanna.almeida")
]

miembros = []
for i, (nombre, apellido, username) in enumerate(miembros_cd):
    user = User.objects.create(
        nombre=nombre,
        apellido=apellido,
        edad=35 + i,
        email=f"{username}@consejo.com",
        username=username,
        consejo=consejo
    )
    user.set_password("admin")
    user.save()
    miembros.append(user)

print(f"Consejo Directivo creado: {consejo.nombre} con miembros {', '.join([m.username for m in miembros])}")
print("✅ Datos iniciales cargados correctamente.")