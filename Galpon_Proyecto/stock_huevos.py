from django.db.models import BigIntegerField, F, Sum, Value
from django.db.models.functions import Cast, Greatest

from .models import (
    CAMPOS_CLASIFICACION, HUEVOS_POR_CUBETA, ControlStockHuevos,
    RegistroProduccion, Venta,
)


def bloquear_stock_huevos():
    ControlStockHuevos.objects.select_for_update().get(pk=1)


def huevos_por_clasificacion(produccion):
    if produccion is None:
        return dict.fromkeys((*CAMPOS_CLASIFICACION, ''), 0)
    huevos = {
        clasificacion: getattr(produccion, campo)
        for clasificacion, campo in CAMPOS_CLASIFICACION.items()
    }
    # Las cubetas registradas conservan el saldo histórico sin tamaño asignado.
    huevos[''] = max(produccion.cantidad_cubetas * HUEVOS_POR_CUBETA - sum(huevos.values()), 0)
    return huevos


def stock_huevos(excluir_venta=None):
    clasificados = sum(Cast(F(campo), BigIntegerField()) for campo in CAMPOS_CLASIFICACION.values())
    capacidad = Cast(F('cantidad_cubetas'), BigIntegerField()) * HUEVOS_POR_CUBETA
    produccion = RegistroProduccion.objects.aggregate(
        **{f'total_{campo}': Sum(campo) for campo in CAMPOS_CLASIFICACION.values()},
        sin_clasificar=Sum(Greatest(capacidad - clasificados, Value(0))),
    )
    disponibles = {
        clasificacion: produccion[f'total_{campo}'] or 0
        for clasificacion, campo in CAMPOS_CLASIFICACION.items()
    }
    disponibles[''] = produccion['sin_clasificar'] or 0

    ventas = Venta.objects.all()
    if excluir_venta is not None:
        ventas = ventas.exclude(pk=excluir_venta)
    for venta in ventas.order_by().values('clasificacion').annotate(cubetas=Sum('cantidad_cubetas')):
        disponibles[venta['clasificacion']] -= venta['cubetas'] * HUEVOS_POR_CUBETA
    return disponibles


def clasificacion_sin_stock(anterior, nueva):
    stock = stock_huevos()
    huevos_anteriores = huevos_por_clasificacion(anterior)
    huevos_nuevos = huevos_por_clasificacion(nueva)
    for clasificacion, disponibles in stock.items():
        saldo = disponibles - huevos_anteriores[clasificacion] + huevos_nuevos[clasificacion]
        if saldo < min(0, disponibles):
            return clasificacion
    return None
