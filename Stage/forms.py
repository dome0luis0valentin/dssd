from django import forms
from .models import Etapa
from CoverageRequest.forms import PedidoCoberturaForm
from TypeCoverage.models import TipoCobertura

class EtapaForm(forms.ModelForm):
    tipo_cobertura = forms.ModelChoiceField(
        queryset=TipoCobertura.objects.all(),
        required=False,
        label="Tipo de cobertura existente",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Seleccione un tipo de cobertura'
        }),
        empty_label="-- Seleccione una opción --"
    )
    nuevo_tipo_cobertura = forms.CharField(
        required=False,
        label="Nuevo tipo de cobertura",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Asistencia médica, Educación, Alimentación...',
        })
    )

    class Meta:
        model = Etapa
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'tipo_cobertura', 'nuevo_tipo_cobertura']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la etapa'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Describa los objetivos y actividades de esta etapa'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
        }

    def save(self, commit=True, proyecto=None):
        # Crear PedidoCobertura directamente
        nuevo_tipo = self.cleaned_data.get('nuevo_tipo_cobertura')
        tipo_cobertura = self.cleaned_data.get('tipo_cobertura')

        if nuevo_tipo:
            from TypeCoverage.models import TipoCobertura
            tipo_obj, created = TipoCobertura.objects.get_or_create(nombre=nuevo_tipo)
            tipo_cobertura = tipo_obj

        # Crear pedido de cobertura
        from CoverageRequest.models import PedidoCobertura
        pedido = PedidoCobertura.objects.create(
            tipo_cobertura=tipo_cobertura,
            estado=False
        )

        # Crear etapa y asignar proyecto y pedido
        instance = super().save(commit=False)
        instance.pedido = pedido
        if proyecto:
            instance.proyecto_id = proyecto
        if commit:
            instance.save()
        return instance


