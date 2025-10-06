from django import forms
from .models import TipoCobertura

class TipoCoberturaForm(forms.ModelForm):
    class Meta:
        model = TipoCobertura
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del tipo de cobertura',
            }),
        }
        labels = {
            'nombre': 'Nombre del tipo de cobertura',
        }
