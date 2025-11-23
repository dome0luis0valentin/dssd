from django import forms
from .models import Proyecto

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "descripcion"]  # originador_id se setea en la vista

