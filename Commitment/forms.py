from django import forms
from .models import Compromiso
#from Stage.models import Etapa
#from CoverageRequest.models import Pedido

class CompromisoForm(forms.ModelForm):
    class Meta:
        model = Compromiso
        fields = ['tipo', 'detalle', 'fecha_inicio', 'fecha_fin', 'responsable']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        pedido = kwargs.pop('pedido', None)
        super().__init__(*args, **kwargs)

        if pedido:
            # Buscar la primera etapa vinculada a este pedido
            etapa = pedido.etapas.first()

            if etapa:
                # Si hay una etapa, usá sus fechas como límites
                self.fields['fecha_inicio'].widget.attrs['min'] = etapa.fecha_inicio.strftime('%Y-%m-%d')
                if etapa.fecha_fin:
                    self.fields['fecha_fin'].widget.attrs['max'] = etapa.fecha_fin.strftime('%Y-%m-%d')
        
        # Las fechas se ocultarán inicialmente; las manejaremos con JS según tipo
        self.fields['fecha_inicio'].required = False
        self.fields['fecha_fin'].required = False
