from django import forms
from django.utils import timezone
from .models import RegistroConsumo
from .models import RegistroMortalidad
from .models import Venta, Alimento, Inventario, GastoOperativo
from .models import RegistroVacunacion


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

    # ✅ CRITERIO 3
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')

        if cantidad is None:
            raise forms.ValidationError("La cantidad es obligatoria.")

        if cantidad <= 0:
            raise forms.ValidationError(
                "La cantidad debe ser un número entero mayor a cero."
            )

        # ✅ CRITERIO 4
        lote = self.cleaned_data.get('lote')
        if lote and cantidad > lote.aves_vivas:
            raise forms.ValidationError(
                "La cantidad de muertes no puede ser mayor al total de aves vivas del lote."
            )

        return cantidad

    # ✅ CRITERIO 6
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')

        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("No se puede registrar una fecha futura.")

        return fecha


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


class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['tipo', 'stock_actual', 'stock_minimo']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'tipo': 'Tipo de insumo',
            'stock_actual': 'Stock actual',
            'stock_minimo': 'Límite mínimo',
        }


class GastoOperativoForm(forms.ModelForm):
    class Meta:
        model = GastoOperativo
        fields = ['categoria', 'descripcion', 'monto']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'categoria': 'Categoría',
            'descripcion': 'Descripción',
            'monto': 'Monto',
        }



# ... (tus otros forms) ...

class RegistroVacunacionForm(forms.ModelForm):
    class Meta:
        model = RegistroVacunacion
        fields = ['lote', 'fecha_aplicacion', 'vacuna', 'gallinas_vacunadas', 'requiere_refuerzo', 'dias_para_refuerzo']
        widgets = {
            'fecha_aplicacion': forms.DateInput(attrs={'type': 'date'}),
        }

    # ✅ CRITERIO 4: Validar fecha futura y cantidad
    def clean_fecha_aplicacion(self):
        fecha = self.cleaned_data.get('fecha_aplicacion')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("No se puede registrar una fecha futura.")
        return fecha

    def clean_gallinas_vacunadas(self):
        cantidad = self.cleaned_data.get('gallinas_vacunadas')
        lote = self.cleaned_data.get('lote')
        
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero.")
        
        if lote and cantidad > lote.aves_vivas:
            raise forms.ValidationError(f"No puedes vacunar más gallinas de las que hay vivas en el lote ({lote.aves_vivas}).")
        
        return cantidad

    # ✅ CRITERIO 3: Advertencia de cobertura parcial
    def clean(self):
        cleaned_data = super().clean()
        lote = cleaned_data.get('lote')
        cantidad = cleaned_data.get('gallinas_vacunadas')

        if lote and cantidad and cantidad < lote.aves_vivas:
            # Lanzamos una advertencia, no un error bloqueante
            self.add_warning = f"Atención: Solo se vacunaron {cantidad} de {lote.aves_vivas} gallinas vivas. Cobertura parcial."
        
        return cleaned_data