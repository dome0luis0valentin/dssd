from django import forms
from .models import PedidoCobertura
from TypeCoverage.models import TipoCobertura

class PedidoCoberturaForm(forms.ModelForm):
    nuevo_tipo_cobertura = forms.CharField(
        required=False,
        label="Nuevo tipo de cobertura",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escriba un nuevo tipo de cobertura si no está en la lista',
        })
    )

    class Meta:
        model = PedidoCobertura
        fields = ['tipo_cobertura', 'nuevo_tipo_cobertura']
        widgets = {
            'tipo_cobertura': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo_cobertura': 'Tipo de cobertura existente',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        nuevo_tipo = self.cleaned_data.get('nuevo_tipo_cobertura')
        if nuevo_tipo:
            tipo_obj, created = TipoCobertura.objects.get_or_create(nombre=nuevo_tipo)
            instance.tipo_cobertura = tipo_obj

        instance.estado = False  # Siempre por defecto en falso

        if commit:
            instance.save()
        return instance
