import re

from django import forms
from django.utils import timezone
from .models import (
    CAMPOS_CLASIFICACION, HUEVOS_POR_CUBETA, Alimento, ClasificacionHuevo, GastoOperativo, Inventario,
    RegistroConsumo, RegistroMortalidad, RegistroProduccion, RegistroVacunacion, Venta,
)


class FechaRegistroForm(forms.ModelForm):
    fecha = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].widget.attrs['max'] = timezone.localdate().isoformat()

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha > timezone.localdate():
            raise forms.ValidationError('La fecha no puede ser futura.')
        return fecha


class RegistroProduccionForm(FechaRegistroForm):
    cantidad_huevos = forms.IntegerField(min_value=1, label='Cantidad de huevos recolectados')
    cantidad_huevos_rotos = forms.IntegerField(min_value=0, required=False, label='Cantidad de huevos rotos')
    cantidad_cubetas = forms.IntegerField(min_value=0, label='Número de cubetas armadas')
    unidad_clasificacion = forms.ChoiceField(
        label='Unidad de la clasificación', required=False,
        choices=[('cubetas', 'Cubetas de 30 huevos'), ('huevos', 'Huevos individuales')],
        initial='cubetas',
    )

    class Meta:
        model = RegistroProduccion
        fields = (
            'fecha', 'cantidad_huevos', 'cantidad_huevos_rotos', 'cantidad_cubetas',
            'unidad_clasificacion', *CAMPOS_CLASIFICACION.values(),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            campos = CAMPOS_CLASIFICACION.values()
            if any(self.initial[campo] % HUEVOS_POR_CUBETA for campo in campos):
                self.initial['unidad_clasificacion'] = 'huevos'
            else:
                for campo in campos:
                    self.initial[campo] //= HUEVOS_POR_CUBETA

    def clean(self):
        datos = super().clean()
        campos = ('cantidad_huevos_rotos', *CAMPOS_CLASIFICACION.values())
        for campo in campos:
            if campo in datos and datos[campo] is None:
                datos[campo] = 0

        total = datos.get('cantidad_huevos')
        rotos = datos.get('cantidad_huevos_rotos')
        if datos.get('unidad_clasificacion') == 'cubetas':
            campos = CAMPOS_CLASIFICACION.values()
            cubetas = datos.get('cantidad_cubetas')
            if cubetas is not None and sum(datos.get(campo, 0) for campo in campos) > cubetas:
                self.add_error('unidad_clasificacion', 'Las cubetas clasificadas no pueden superar las cubetas armadas.')
            for campo in campos:
                if campo in datos:
                    datos[campo] *= HUEVOS_POR_CUBETA
        if total is not None and rotos is not None:
            if rotos > total:
                self.add_error('cantidad_huevos_rotos', 'Los huevos rotos no pueden superar el total recolectado.')
            elif sum(datos.get(campo, 0) for campo in CAMPOS_CLASIFICACION.values()) > total - rotos:
                self.add_error(None, 'Los huevos clasificados no pueden superar los huevos recolectados menos los rotos.')
        return datos



class RegistroConsumoForm(forms.ModelForm):
    class Meta:
        model = RegistroConsumo
        fields = ['poblacion_gallinas', 'bultos_consumidos']
        widgets = {
            'poblacion_gallinas': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'bultos_consumidos': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }
        labels = {
            'poblacion_gallinas': 'Población de gallinas',
            'bultos_consumidos': 'Bultos de alimento gastados hoy',
        }

class FormularioConLote(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and 'lote' not in self.initial:
            lotes = list(self.fields['lote'].queryset.values_list('pk', flat=True)[:2])
            if len(lotes) == 1:
                self.initial['lote'] = lotes[0]


class RegistroMortalidadForm(FormularioConLote):
    class Meta:
        model = RegistroMortalidad
        fields = ['lote', 'fecha', 'cantidad', 'causa', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
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
            raise forms.ValidationError(
                "La cantidad debe ser mayor a cero."
            )

        if lote:
            disponibles = lote.aves_vivas

            # Al editar, devolver temporalmente al cálculo
            # las muertes del registro actual.
            if self.instance.pk and self.instance.lote_id == lote.pk:
                disponibles += self.instance.cantidad

            if cantidad > disponibles:
                raise forms.ValidationError(
                    f"No puedes registrar más de "
                    f"{max(0, disponibles)} muertes en este lote."
                )

        return cantidad

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        lote = self.cleaned_data.get('lote')

        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError(
                "No se puede registrar una fecha futura."
            )

        if fecha and lote and fecha < lote.fecha_ingreso:
            raise forms.ValidationError(
                "La fecha no puede ser anterior al ingreso del lote."
            )

        return fecha



class PrecioCubetaField(forms.DecimalField):
    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip()
            if re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]{1,2})?', value):
                value = value.replace('.', '')
            if re.fullmatch(r'[0-9]+,[0-9]{1,2}', value):
                value = value.replace(',', '.')
        return super().to_python(value)


class VentaForm(FechaRegistroForm):
    clasificacion = forms.ChoiceField(
        label='Clasificación',
        choices=[('', 'Selecciona una clasificación'), *ClasificacionHuevo.choices, ('sin_clasificar', 'Sin clasificar')],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.instance.clasificacion:
            self.initial['clasificacion'] = 'sin_clasificar'

    def clean_clasificacion(self):
        clasificacion = self.cleaned_data['clasificacion']
        return '' if clasificacion == 'sin_clasificar' else clasificacion

    class Meta:
        model = Venta
        fields = ['fecha', 'cliente', 'clasificacion', 'cantidad_cubetas', 'precio_unitario']
        widgets = {
            'cantidad_cubetas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'decimal'}),
        }
        field_classes = {'precio_unitario': PrecioCubetaField}
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

    stock_actual = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '0',
            'placeholder': 'Ingrese una cantidad'
        })
    )

    stock_minimo = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '0',
            'placeholder': 'Ingrese una cantidad'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound and not self.instance.pk:
            self.fields['stock_actual'].initial = None
            self.fields['stock_minimo'].initial = None

    class Meta:
        model = Inventario
        fields = ['tipo', 'stock_actual', 'stock_minimo']

        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

        labels = {
            'tipo': 'Tipo de insumo',
            'stock_actual': 'Stock actual',
            'stock_minimo': 'Límite mínimo',
        }



class AgregarBultosForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=Inventario.TIPOS_INSUMO,
        label='Tipo de insumo',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    cantidad = forms.DecimalField(
        label='Cantidad de bultos que ingresan',
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': 'Ej. 10'
        })
    )



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

class RegistroVacunacionForm(FormularioConLote):
    class Meta:
        model = RegistroVacunacion
        fields = ['lote', 'fecha_aplicacion', 'vacuna', 'gallinas_vacunadas', 'requiere_refuerzo', 'dias_para_refuerzo']
        widgets = {
            'fecha_aplicacion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    # ✅ CRITERIO 4: Validar fecha futura y cantidad
    def clean_fecha_aplicacion(self):
        fecha = self.cleaned_data.get('fecha_aplicacion')
        if fecha and fecha > timezone.localdate():
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
