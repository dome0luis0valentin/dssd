from django import forms
from .models import Compromiso

class CompromisoForm(forms.ModelForm):
    class Meta:
        model = Compromiso
        # quitamos 'responsable'
        fields = ['tipo', 'detalle', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.pedido = kwargs.pop('pedido', None)
        super().__init__(*args, **kwargs)

        if self.pedido:
            # Tomamos la primera etapa vinculada al pedido
            etapa = self.pedido.etapas.first() if hasattr(self.pedido, 'etapas') else None

            if etapa:
                # Configuramos los límites visuales por defecto
                self.fields['fecha_inicio'].widget.attrs['min'] = etapa.fecha_inicio.strftime('%Y-%m-%d')
                if etapa.fecha_fin:
                    self.fields['fecha_fin'].widget.attrs['max'] = etapa.fecha_fin.strftime('%Y-%m-%d')

        # Las fechas se ocultarán inicialmente; se mostrarán según tipo (JS)
        self.fields['fecha_inicio'].required = False
        self.fields['fecha_fin'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        # Validamos solo si hay un pedido y tipo parcial
        if self.pedido and tipo == 'parcial':
            etapa = self.pedido.etapas.first() if hasattr(self.pedido, 'etapas') else None
            if etapa:
                # Fecha de inicio dentro del rango
                if fecha_inicio and (fecha_inicio < etapa.fecha_inicio or (etapa.fecha_fin and fecha_inicio > etapa.fecha_fin)):
                    self.add_error('fecha_inicio', f'La fecha de inicio debe estar entre {etapa.fecha_inicio} y {etapa.fecha_fin}.')
                # Fecha de fin dentro del rango
                if fecha_fin and (fecha_fin < etapa.fecha_inicio or (etapa.fecha_fin and fecha_fin > etapa.fecha_fin)):
                    self.add_error('fecha_fin', f'La fecha de fin debe estar entre {etapa.fecha_inicio} y {etapa.fecha_fin}.')

        return cleaned_data
