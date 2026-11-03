from django.contrib import admin
from .models import RegistroVacunacion
from .models import (
    Lote,
    RegistroMortalidad,
    RegistroProduccion,
    RegistroConsumo,
    Venta,
    Alimento,
    Inventario,
    AlertaStock,
    GastoOperativo,
)


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_ingreso', 'cantidad_inicial', 'aves_vivas')
    search_fields = ('nombre',)


@admin.register(RegistroMortalidad)
class RegistroMortalidadAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'cantidad', 'causa', 'registrado_por')
    list_filter = ('causa', 'lote')
    date_hierarchy = 'fecha'


@admin.register(RegistroProduccion)
class RegistroProduccionAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cantidad_huevos', 'cantidad_cubetas', 'cantidad_huevos_rotos')
    date_hierarchy = 'fecha'


@admin.register(RegistroConsumo)
class RegistroConsumoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'poblacion_gallinas', 'bultos_consumidos')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cliente', 'cantidad_cubetas', 'total')
    search_fields = ('cliente',)
    date_hierarchy = 'fecha'


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'cantidad_bultos', 'costo_total', 'proveedor')
    list_filter = ('tipo',)


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'stock_actual', 'stock_minimo', 'stock_bajo')


@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ('inventario', 'activa', 'creada_en')
    list_filter = ('activa',)


@admin.register(GastoOperativo)
class GastoOperativoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'categoria', 'descripcion', 'monto')
    list_filter = ('categoria',)


@admin.register(RegistroVacunacion)
class RegistroVacunacionAdmin(admin.ModelAdmin):
    list_display = ('vacuna', 'lote', 'fecha_aplicacion', 'gallinas_vacunadas', 'requiere_refuerzo', 'fecha_proximo_refuerzo')
    list_filter = ('vacuna', 'requiere_refuerzo')