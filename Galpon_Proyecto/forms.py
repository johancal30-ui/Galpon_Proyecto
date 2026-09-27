from django import forms
from .models import RegistroConsumo
from .models import RegistroMortalidad
from .models import Venta


class RegistroConsumoForm(forms.ModelForm):
    class Meta:
        model = RegistroConsumo
        fields = ['poblacion_gallinas', 'bultos_consumidos', 'kilos_por_bulto', 'stock_disponible']
        widgets = {
            'poblacion_gallinas': forms.NumberInput(attrs={'class': 'form-control'}),
            'bultos_consumidos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'kilos_por_bulto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_disponible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'poblacion_gallinas': 'Población de gallinas',
            'bultos_consumidos': 'Bultos consumidos',
            'kilos_por_bulto': 'Kilos por bulto',
            'stock_disponible': 'Stock disponible (bultos)',
        }

class RegistroMortalidadForm(forms.ModelForm):
    class Meta:
        model = RegistroMortalidad
        fields = ['lote', 'fecha', 'cantidad', 'causa', 'observaciones']

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'cantidad_cubetas', 'precio_unitario']
        widgets = {
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_cubetas': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'cliente': 'Cliente',
            'cantidad_cubetas': 'Cantidad de cubetas',
            'precio_unitario': 'Precio por cubeta',
        }