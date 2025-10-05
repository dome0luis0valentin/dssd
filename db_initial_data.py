import os
import django

# Configurar Django para poder usar los modelos
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

# --- CREAR 5 ONGs con un usuario cada una ---
for i in range(1, 6):
    ong = ONG.objects.create(nombre=f"ONG{i}")
    
    usuario = User.objects.create(
        nombre=f"UsuarioONG{i}",
        apellido=f"Apellido{i}",
        edad=25 + i,
        email=f"user{i}@correo.com"
    )
    usuario.set_password("123")
    usuario.save()
    
    usuario.ong = ong
    usuario.save()
    print(f"ONG creada: {ong.nombre} con usuario {usuario.nombre} {usuario.apellido}")

# --- CREAR Consejo Directivo con 3 usuarios ---
consejo = ConsejoDirectivo.objects.create(nombre="Consejo Directivo Principal")

miembros = []
for i in range(1, 4):
    user = User.objects.create(
        nombre=f"MiembroCD{i}",
        apellido=f"ApellidoCD{i}",
        edad=30 + i,
        email=f"miembro{i}@consejo.com",
        consejo=consejo
    )
    user.set_password("123")
    user.save()
    miembros.append(user)
    
usuario = User.objects.create(
    nombre="Walter",
    apellido="Bates",
    edad=25 + i,
    email="walter.bates@correo.com"
)
usuario.set_password("admin")
usuario.save()

print(f"Consejo Directivo creado: {consejo.nombre} con miembros {', '.join([m.nombre for m in miembros])}")
print("Datos iniciales cargados correctamente.")
