from django import forms
from .models import RegistroConsumo
from .models import RegistroMortalidad
from .models import Venta, Alimento


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
            'cantidad_cubetas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
        }
        labels = {
            'cliente': 'Cliente',
            'cantidad_cubetas': 'Cantidad de cubetas',
            'precio_unitario': 'Precio por cubeta',
        }

    def clean_cliente(self):
        cliente = self.cleaned_data.get('cliente')
        if not cliente or not cliente.strip():
            raise forms.ValidationError('El nombre del cliente es obligatorio.')
        return cliente.strip()

    def clean_cantidad_cubetas(self):
        cantidad = self.cleaned_data.get('cantidad_cubetas')
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError('La cantidad de cubetas debe ser mayor a cero.')
        return cantidad

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio is None or precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a cero.')
        return precio

class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = ['tipo', 'cantidad_bultos', 'kilos_por_bulto', 'costo_unitario', 'proveedor']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_bultos': forms.NumberInput(attrs={'class': 'form-control'}),
            'kilos_por_bulto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo': 'Tipo de alimento',
            'cantidad_bultos': 'Cantidad de bultos',
            'kilos_por_bulto': 'Kilos por bulto',
            'costo_unitario': 'Costo unitario por bulto',
            'proveedor': 'Proveedor',
        }