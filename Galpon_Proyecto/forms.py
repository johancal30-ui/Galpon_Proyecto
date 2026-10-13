from django import forms
from accounts.models import RegistroMortalidad, RegistroConsumo, RegistroProduccion


class RegistroMortalidadForm(forms.ModelForm):
    class Meta:
        model = RegistroMortalidad
        fields = ['lote', 'fecha', 'cantidad', 'causa', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Opcional'}),
        }
        labels = {
            'lote': 'Lote',
            'fecha': 'Fecha',
            'cantidad': 'Cantidad de aves muertas',
            'causa': 'Causa',
            'observaciones': 'Observaciones',
        }
        help_texts = {
            'cantidad': 'Número entero, mayor a cero, y no mayor al total de aves vivas del lote.',
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        lote = self.cleaned_data.get('lote')

        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")

        if lote and cantidad > lote.aves_vivas:
            raise forms.ValidationError(
                f"No puedes registrar más muertes que las aves vivas del lote "
                f"({lote.aves_vivas} disponibles)."
            )
        return cantidad


class RegistroConsumoForm(forms.ModelForm):
    class Meta:
        model = RegistroConsumo
        fields = '__all__'  # o especifica los campos que quieras, ej: ['lote', 'fecha', ...]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }


class RegistroProduccionForm(forms.ModelForm):
    class Meta:
        model = RegistroProduccion
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }