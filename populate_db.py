#!/usr/bin/env python
import os
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dssd.settings")
django.setup()

from ONG.models import ONG
from BoardOfDirectors.models import ConsejoDirectivo
from user.models import User

# Limpiar datos previos
ONG.objects.all().delete()
ConsejoDirectivo.objects.all().delete()
User.objects.all().delete()

def random_name(prefix, i, j):
    return f"{prefix}{i}{j}"

def random_email(nombre, apellido):
    # Email más corto
    return f"{nombre.lower()}{apellido.lower()}@ex.com"

DEFAULT_PASSWORD = "1234"  # contraseña corta

# Crear 10 ONGs con 3 usuarios cada una
for i in range(1, 11):
    ong = ONG.objects.create(nombre=f"ONG{i}")

    for j in range(1, 4):
        nombre = random_name("O", i, j)
        apellido = random_name("A", i, j)
        email = random_email(nombre, apellido)
        user = User(
            nombre=nombre,
            apellido=apellido,
            edad=random.randint(20, 60),
            email=email,
            password=DEFAULT_PASSWORD,
            consejo=None
        )
        user.save()
        ong.usuarios.add(user)

# Crear 10 Consejos Directivos con 3 miembros cada uno
for i in range(1, 11):
    consejo = ConsejoDirectivo.objects.create(nombre=f"Consejo{i}")

    for j in range(1, 4):
        nombre = random_name("C", i, j)
        apellido = random_name("A", i, j)
        email = random_email(nombre, apellido)
        user = User(
            nombre=nombre,
            apellido=apellido,
            edad=random.randint(30, 70),
            email=email,
            password=DEFAULT_PASSWORD,
            consejo=consejo
        )
        user.save()

print("✅ Se crearon 10 ONGs con 3 usuarios cada una y 10 Consejos Directivos con 3 miembros cada uno con contraseña corta")
