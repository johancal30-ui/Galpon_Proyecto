from django import forms
from django.utils import timezone
from .models import RegistroMortalidad


class RegistroMortalidadForm(forms.ModelForm):
    class Meta:
        model = RegistroMortalidad
        fields = ['lote', 'fecha', 'cantidad', 'causa', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        error_messages = {
            'lote': {'required': 'Debes seleccionar un lote.'},
            'fecha': {'required': 'Debes ingresar la fecha.'},
            'cantidad': {
                'required': 'Debes ingresar la cantidad de aves muertas.',
                'invalid': 'La cantidad debe ser un número entero mayor a cero.',
            },
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser un número entero mayor a cero.')
        return cantidad

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError('No se puede registrar una fecha futura.')
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        lote = cleaned_data.get('lote')
        cantidad = cleaned_data.get('cantidad')

        if lote and cantidad:
            if cantidad > lote.aves_vivas:
                self.add_error(
                    'cantidad',
                    'La cantidad de muertes no puede ser mayor al total de aves vivas del lote.'
                )
        return cleaned_data