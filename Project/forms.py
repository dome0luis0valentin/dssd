from django import forms
from .models import Proyecto
from Stage.models import Etapa

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "descripcion", "estado"]  # originador se setea en la vista


class EtapaForm(forms.ModelForm):
    class Meta:
        model = Etapa
        fields = ["nombre", "descripcion", "fecha_inicio", "fecha_fin"]
