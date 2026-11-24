from copy import copy
from django.forms import Select
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import date
from datetime import datetime
from .models import (RegistroProduccion, RegistroConsumo, RegistroMortalidad,Venta, Alimento, Inventario, AlertaStock, GastoOperativo)
from .forms import (RegistroConsumoForm, RegistroMortalidadForm,VentaForm, AlimentoForm, InventarioForm,AgregarBultosForm, GastoOperativoForm)
from django.db import transaction#creado por johan para descargar reporte excel:
from datetime import date
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .reportes import construir_reporte
# creado por johan para CLIENTESS
from .models import Cliente

from .models import RegistroVacunacion 
from .forms import RegistroVacunacionForm 

from datetime import datetime
from django.db.models import Sum
from .forms import RegistroProduccionForm
from .models import HUEVOS_POR_CUBETA
from .stock_huevos import bloquear_stock_huevos, clasificacion_sin_stock, stock_huevos
from django.core.paginator import Paginator


def registrar_produccion(request):
    return guardar_produccion(request)


def editar_produccion(request, pk):
    return guardar_produccion(request, pk)


def guardar_produccion(request, pk=None):
    if request.method == 'POST':
        with transaction.atomic():
            bloquear_stock_huevos()
            anterior = get_object_or_404(RegistroProduccion, pk=pk) if pk is not None else None
            # ModelForm actualiza su instancia al validar.
            form = RegistroProduccionForm(request.POST, instance=copy(anterior))
            if form.is_valid():
                nuevo = form.save(commit=False)
                faltante = clasificacion_sin_stock(anterior, nuevo)
                if faltante is None:
                    nuevo.save()
                    messages.success(request, 'Registro actualizado exitosamente' if pk else 'Registro guardado exitosamente')
                    return redirect('registrar_produccion')
                form.add_error(None, error_reduccion_stock(faltante))
    else:
        instancia = get_object_or_404(RegistroProduccion, pk=pk) if pk is not None else None
        inicial = {'fecha': timezone.localdate()} if instancia is None else None
        form = RegistroProduccionForm(instance=instancia, initial=inicial)

    contexto = {'form': form}
    if pk is not None:
        return render(request, 'produccion_editar.html', contexto)
    contexto['registros'] = RegistroProduccion.objects.all()
    return render(request, 'produccion.html', contexto)


def error_reduccion_stock(clasificacion):
    etiqueta = clasificacion or 'Sin clasificar'
    return f'El cambio dejaría sin respaldo ventas de cubetas de la clasificación {etiqueta}.'


def eliminar_produccion(request, pk):
    registro = get_object_or_404(RegistroProduccion, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            bloquear_stock_huevos()
            registro = get_object_or_404(RegistroProduccion, pk=pk)
            faltante = clasificacion_sin_stock(registro, None)
            if faltante is None:
                registro.delete()
                messages.success(request, 'Registro eliminado exitosamente')
                return redirect('registrar_produccion')
            messages.error(request, error_reduccion_stock(faltante))
            return redirect('registrar_produccion')

    return render(request, 'produccion_eliminar.html', {'registro': registro})


# CONSUMO DIARIO (JHON)

def registrar_consumo(request):
    if request.method == 'POST':
        form = RegistroConsumoForm(request.POST)

        if form.is_valid():
            registro = form.save(commit=False)

            try:
                with transaction.atomic():
                    # Consultar el inventario de alimento
                    inventario = Inventario.objects.select_for_update().get(
                        tipo='alimento'
                    )

                    if registro.bultos_consumidos > inventario.stock_actual:
                        form.add_error(
                            'bultos_consumidos',
                            f'Solo quedan {inventario.stock_actual} '
                            f'bultos de alimento disponibles.'
                        )
                    else:
                        # Guardar el stock existente antes del consumo
                        registro.stock_disponible = inventario.stock_actual
                        registro.save()

                        # Descontar el consumo del inventario general
                        inventario.stock_actual -= registro.bultos_consumidos
                        inventario.save(
                            update_fields=['stock_actual', 'actualizado_en']
                        )

                        # Actualizar las alertas de stock
                        inventario.verificar_alerta()

                        # Mostrar advertencia si el consumo es anómalo
                        if registro.es_consumo_anomalo:
                            messages.warning(
                                request,
                                f"Advertencia: Consumo anómalo "
                                f"({registro.consumo_gramos_por_gallina} "
                                f"g/gallina/día) para "
                                f"{registro.poblacion_gallinas} gallinas. "
                                f"Verifique un posible desperdicio o "
                                f"problema de nutrición."
                            )

                        # Mostrar éxito tanto si es normal como anómalo
                        messages.success(
                            request,
                            f"Registro guardado. Consumo: "
                            f"{registro.consumo_gramos_por_gallina} "
                            f"g/gallina/día. "
                            f"Stock restante: "
                            f"{inventario.stock_actual} bultos."
                        )

                        return redirect('registrar_consumo')

            except Inventario.DoesNotExist:
                form.add_error(
                    None,
                    'No existe un inventario de alimento configurado. '
                    'Configure el inventario antes de registrar consumos.'
                )

    else:
        form = RegistroConsumoForm()

    registros = RegistroConsumo.objects.all().order_by('-fecha', '-id')
    inventario = Inventario.objects.filter(tipo='alimento').first()

    return render(
        request,
        'consumo_form.html',
        {
            'form': form,
            'registros': registros,
            'inventario': inventario,
        }
    )


# MORTALIDAD (JEFFRY)
@login_required
def mortalidad_lista(request):
    registros = RegistroMortalidad.objects.select_related('lote', 'registrado_por').all()
    total_cantidad = registros.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    lotes_afectados = registros.values('lote').distinct().count()
    total_registros = registros.count()

    # NUEVO: Calcular los totales del inventario de TODOS los lotes
    from .models import Lote
    lotes = Lote.objects.all()
    total_inicial_global = sum(lote.cantidad_inicial for lote in lotes)
    total_actual_global = sum(lote.aves_vivas for lote in lotes)

    return render(request, 'mortalidad.html', {
        'registros': registros,
        'total_cantidad': total_cantidad,
        'lotes_afectados': lotes_afectados,
        'total_registros': total_registros,
        'total_inicial_global': total_inicial_global,  # <-- Nuevo
        'total_actual_global': total_actual_global,    # <-- Nuevo
    })

@login_required
def mortalidad_registrar(request):
    if request.method == 'POST':
        form = RegistroMortalidadForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            registro.save()
            messages.success(request, 'Registro de mortalidad guardado correctamente.')
            return redirect('mortalidad_lista')
    else:
        form = RegistroMortalidadForm(initial={'fecha': timezone.localdate()})

    return render(request, 'registrar.html', {'form': form})


@login_required
def mortalidad_eliminar(request, pk):
    registro = get_object_or_404(RegistroMortalidad, pk=pk)
    
    if request.method == 'POST':
        registro.delete()
        messages.success(request, 'Registro de mortalidad eliminado.')
        return redirect('mortalidad_lista')

    # Si es GET, mostramos la pantalla de confirmación
    return render(request, 'mortalidad_eliminar.html', {'registro': registro})


@login_required
def mortalidad_editar(request, pk):
    registro = get_object_or_404(RegistroMortalidad, pk=pk)
    
    if request.method == 'POST':
        form = RegistroMortalidadForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro de mortalidad actualizado correctamente.')
            return redirect('mortalidad_lista')
    else:
        form = RegistroMortalidadForm(instance=registro)

    return render(request, 'mortalidad_editar.html', {'form': form, 'registro': registro})

# VENTAS (ANDRÉS)

@login_required
def registrar_venta(request):
    hoy = timezone.localdate()
    form = VentaForm(initial={'fecha': hoy})
    if request.method == 'POST':
        with transaction.atomic():
            bloquear_stock_huevos()
            form = VentaForm(request.POST)
            if guardar_venta(form, request.user):
                messages.success(request, f'Venta registrada. Total: ${form.instance.total}')
                return redirect('registrar_venta')

    existencias = stock_huevos()
    stock_por_clasificacion = [
        (clasificacion or 'Sin clasificar', max(huevos // HUEVOS_POR_CUBETA, 0))
        for clasificacion, huevos in existencias.items()
    ]
    ingresos_hoy = Venta.objects.filter(fecha=hoy).aggregate(total=Sum('total'))['total'] or 0
    filtros_clasificacion = form.fields['clasificacion'].choices[1:]
    filtro = request.GET.get('clasificacion', '')
    ventas = Venta.objects.order_by('-fecha', '-pk')
    if filtro in dict(filtros_clasificacion):
        ventas = ventas.filter(clasificacion='' if filtro == 'sin_clasificar' else filtro)
    for venta in ventas:
        venta.total_form = f"{int(venta.total):,}".replace(",", ".")
        venta.precio_form = f"{int(venta.precio_unitario):,}".replace(",", ".")

    return render(request, 'venta.html', {
        'form': form,
        'hoy': hoy,
        'ventas': ventas,
        'stock_disponible': sum(cubetas for _, cubetas in stock_por_clasificacion),
        'stock_por_clasificacion': stock_por_clasificacion,
        'filtros_clasificacion': filtros_clasificacion,
        'filtro_clasificacion': filtro,
        'ingresos_hoy': f"{int(ingresos_hoy):,}".replace(",", "."),
    })


def guardar_venta(form, usuario):
    if not form.is_valid():
        return False

    venta = form.save(commit=False)
    huevos_disponibles = stock_huevos(excluir_venta=venta.pk)[venta.clasificacion]
    cubetas_disponibles = max(huevos_disponibles // HUEVOS_POR_CUBETA, 0)
    if venta.cantidad_cubetas > cubetas_disponibles:
        etiqueta = venta.get_clasificacion_display() or 'Sin clasificar'
        form.add_error('cantidad_cubetas', f'Solo hay {cubetas_disponibles} cubetas disponibles de la clasificación {etiqueta}.')
        return False

    venta.cantidad_huevos = venta.cantidad_cubetas * HUEVOS_POR_CUBETA
    if venta.pk is None:
        venta.registrado_por = usuario
    venta.save()
    return True


@login_required
def editar_venta(request, pk):
    if request.method == 'POST':
        with transaction.atomic():
            bloquear_stock_huevos()
            venta = get_object_or_404(Venta, pk=pk)
            form = VentaForm(request.POST, instance=venta)
            if guardar_venta(form, request.user):
                messages.success(request, 'Venta actualizada correctamente.')
                return redirect('registrar_venta')
    else:
        venta = get_object_or_404(Venta, pk=pk)
        form = VentaForm(instance=venta)

    clientes = list(Cliente.objects.values_list('nombre', flat=True).distinct())
    cliente_actual = form['cliente'].value()
    if cliente_actual and cliente_actual not in clientes:
        clientes.append(cliente_actual)
    form.fields['cliente'].widget = Select(choices=[('', 'Selecciona un cliente'), *((nombre, nombre) for nombre in clientes)])

    return render(request, 'venta_editar.html', {'form': form, 'venta': venta})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            bloquear_stock_huevos()
            get_object_or_404(Venta, pk=pk).delete()
        messages.success(request, 'Venta eliminada.')
        return redirect('registrar_venta')

    venta.total_form = f"{int(venta.total):,}".replace(",", ".")
    return render(request, 'venta_eliminar.html', {'venta': venta})


#(ALIMENTO ANDRRES)

def formato_cop(valor):
    """Formatea un número como moneda colombiana: 200000 -> $200.000"""
    if valor is None:
        return "$0"
    try:
        return "${:,.0f}".format(float(valor)).replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

@login_required
def registrar_alimento(request):
    form = AlimentoForm()
    error_manual = None

    if request.method == 'POST':
        form = AlimentoForm(request.POST)

        tipo = request.POST.get('tipo', '').strip()
        cantidad = request.POST.get('cantidad_bultos', '')
        kilos = request.POST.get('kilos_por_bulto', '')
        costo = request.POST.get('costo_unitario', '')
        proveedor = request.POST.get('proveedor', '').strip()

        # Validar tipo
        if not tipo:
            error_manual = "Debes seleccionar un tipo de alimento."

                # Validar cantidad
        elif not cantidad:
            error_manual = "La cantidad de bultos es obligatoria."
        else:
            try:
                cantidad_int = int(cantidad)
                if cantidad_int <= 0:
                    error_manual = "La cantidad debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "La cantidad debe ser un número entero."

        # Validar kilos por bulto (CORREGIDO PARA FORMATO COLOMBIA)
        if error_manual is None:
            if not kilos:
                error_manual = "Los kilos por bulto son obligatorios."
            else:
                try:
                    # Limpiamos el string: quitamos puntos de miles y cambiamos coma por punto decimal
                    kilos_limpio = str(kilos).replace('.', '').replace(',', '.')
                    kilos_float = float(kilos_limpio)
                    if kilos_float <= 0:
                        error_manual = "Los kilos por bulto deben ser mayores a cero."
                except (ValueError, TypeError):
                    error_manual = "Los kilos deben ser un número válido."

        # Validar costo unitario (CORREGIDO PARA FORMATO COLOMBIA)
        if error_manual is None:
            if not costo:
                error_manual = "El costo unitario es obligatorio."
            else:
                try:
                    # Limpiamos el string: quitamos puntos de miles y cambiamos coma por punto decimal
                    costo_limpio = str(costo).replace('.', '').replace(',', '.')
                    costo_float = float(costo_limpio)
                    if costo_float <= 0:
                        error_manual = "El costo debe ser mayor a cero."
                except (ValueError, TypeError):
                    error_manual = "El costo debe ser un número válido."

        # Validar proveedor
        if error_manual is None and not proveedor:
            error_manual = "El nombre del proveedor es obligatorio."

        # Si todo está bien, guardar
        if error_manual is None:
            alimento = Alimento(
                tipo=tipo,
                cantidad_bultos=cantidad_int,
                kilos_por_bulto=kilos_float,
                costo_unitario=costo_float,
                proveedor=proveedor,
                registrado_por=request.user,
            )
            alimento.save()
            
            # 👇 AQUÍ ESTÁ EL CAMBIO: Usamos formato_cop en lugar de imprimir el float directo
            messages.success(request, f'Ingreso registrado. Costo total: {formato_cop(alimento.costo_total)}')
            
            return redirect('registrar_alimento')

    # Calcular el stock por tipo (suma de todos los registros)
    stock_por_tipo = []
    for codigo, nombre in Alimento.TIPOS:
        registros = Alimento.objects.filter(tipo=codigo)
        total_bultos = registros.aggregate(Sum('cantidad_bultos'))['cantidad_bultos__sum'] or 0
        costo_total = registros.aggregate(Sum('costo_total'))['costo_total__sum'] or 0
        ultimo = registros.order_by('-fecha').first()
        proveedor_ultimo = ultimo.proveedor if ultimo else 'Sin registrar'

        if total_bultos > 0:
            stock_por_tipo.append({
                'tipo': nombre,
                'total_bultos': total_bultos,
                'costo_total': costo_total,
                'proveedor': proveedor_ultimo,
            })

    # Historial paginado (5 por página)
    historial_qs = Alimento.objects.all().order_by('-fecha', '-id')
    paginator = Paginator(historial_qs, 5)
    historial = paginator.get_page(request.GET.get('page'))
    rango_paginas = paginator.get_elided_page_range(
        historial.number, on_each_side=1, on_ends=1
    )

        # Cálculo del total invertido por período
    total_invertido = None
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    if fecha_desde and fecha_hasta:
        try:
            consulta = Alimento.objects.filter(
                fecha__gte=fecha_desde,
                fecha__lte=fecha_hasta
            )
            total_invertido = consulta.aggregate(Sum('costo_total'))['costo_total__sum'] or 0
        except Exception:
            total_invertido = None

    if total_invertido is not None:
        total_invertido = formato_cop(total_invertido)

    # Para conservar el filtro de fechas al cambiar de página
    filtros = ''
    if fecha_desde:
        filtros += f'&fecha_desde={fecha_desde}'
    if fecha_hasta:
        filtros += f'&fecha_hasta={fecha_hasta}'

    # Formatear costos solo de los registros de la página actual
    for a in historial:
        a.costo_unit_form = formato_cop(a.costo_unitario)
        a.costo_total_form = formato_cop(a.costo_total)

    for s in stock_por_tipo:
        s['costo_total_form'] = formato_cop(s['costo_total'])

    return render(request, 'alimento.html', {
        'form': form,
        'stock_por_tipo': stock_por_tipo,
        'historial': historial,
        'rango_paginas': rango_paginas,
        'total_registros': paginator.count,
        'filtros': filtros,
        'error_manual': error_manual,
        'total_invertido': total_invertido,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })

@login_required
def editar_alimento(request, pk):
    alimento = get_object_or_404(Alimento, pk=pk)
    form = AlimentoForm(instance=alimento)
    error_manual = None

    if request.method == 'POST':
        form = AlimentoForm(request.POST, instance=alimento)
        # Reutilizamos la misma validación que en registrar_alimento.
        # Para no duplicar código, hacemos la validación básica aquí.

        tipo = request.POST.get('tipo', '').strip()
        cantidad = request.POST.get('cantidad_bultos', '')
        kilos = request.POST.get('kilos_por_bulto', '')
        costo = request.POST.get('costo_unitario', '')
        proveedor = request.POST.get('proveedor', '').strip()

        if not tipo:
            error_manual = "Debes seleccionar un tipo de alimento."
        elif not cantidad:
            error_manual = "La cantidad de bultos es obligatoria."
        else:
            try:
                cantidad_int = int(cantidad)
                if cantidad_int <= 0:
                    error_manual = "La cantidad debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "La cantidad debe ser un número entero."

        if error_manual is None:
            try:
                kilos_float = float(kilos)
                if kilos_float <= 0:
                    error_manual = "Los kilos por bulto deben ser mayores a cero."
            except (ValueError, TypeError):
                error_manual = "Los kilos deben ser un número válido."

        if error_manual is None:
            try:
                costo_float = float(costo)
                if costo_float <= 0:
                    error_manual = "El costo debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "El costo debe ser un número válido."

        if error_manual is None and not proveedor:
            error_manual = "El nombre del proveedor es obligatorio."

        if error_manual is None:
            alimento.tipo = tipo
            alimento.cantidad_bultos = cantidad_int
            alimento.kilos_por_bulto = kilos_float
            alimento.costo_unitario = costo_float
            alimento.proveedor = proveedor
            alimento.save()
            messages.success(request, 'Ingreso actualizado correctamente.')
            return redirect('registrar_alimento')
            
    alimento.costo_form = f"{int(alimento.costo_unitario):,}".replace(",", ".")

    return render(request, 'alimento_editar.html', {
        'form': form,
        'alimento': alimento,
        'error_manual': error_manual,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def eliminar_alimento(request, pk):
    alimento = get_object_or_404(Alimento, pk=pk)
    if request.method == 'POST':
        alimento.delete()
        messages.success(request, 'Ingreso eliminado.')
        return redirect('registrar_alimento')

    return render(request, 'alimento_eliminar.html', {'alimento': alimento})

# INVENTARIO Y ALERTAS DE STOCK (JHON)

def inventario(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)

        if form.is_valid():
            datos = form.save(commit=False)

            # Reutilizar el inventario existente del mismo tipo
            inventario_existente = Inventario.objects.filter(
                tipo=datos.tipo
            ).first()

            if inventario_existente:
                inventario_existente.stock_actual = datos.stock_actual
                inventario_existente.stock_minimo = datos.stock_minimo
                inventario_existente.save()
                inventario_guardado = inventario_existente
            else:
                datos.save()
                inventario_guardado = datos

            inventario_guardado.verificar_alerta()

            if inventario_guardado.stock_bajo:
                messages.warning(
                    request,
                    f"⚠️ Stock bajo de "
                    f"{inventario_guardado.get_tipo_display()}: "
                    f"{inventario_guardado.stock_actual}. "
                    f"Mínimo: {inventario_guardado.stock_minimo}."
                )
            else:
                messages.success(
                    request,
                    f"Inventario de "
                    f"{inventario_guardado.get_tipo_display()} "
                    f"actualizado correctamente."
                )

            return redirect('inventario')
    else:
        form = InventarioForm()

    inventarios = Inventario.objects.all()
    alertas = AlertaStock.objects.filter(activa=True)

    return render(
        request,
        'inventario.html',
        {
            'form': form,
            'inventarios': inventarios,
            'alertas': alertas,
        }
    )


# AGREGAR BULTOS AL INVENTARIO
@login_required
def agregar_bultos(request):
    if request.method == 'POST':
        form = AgregarBultosForm(request.POST)

        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            cantidad = form.cleaned_data['cantidad']

            inventario_obj = Inventario.objects.filter(
                tipo=tipo
            ).first()

            if inventario_obj:
                inventario_obj.stock_actual += cantidad
                inventario_obj.save()
                inventario_obj.verificar_alerta()

                messages.success(
                    request,
                    f'Se agregaron {cantidad} unidades al inventario. '
                    f'Stock actual: {inventario_obj.stock_actual}.'
                )
            else:
                messages.error(
                    request,
                    'Primero debes registrar ese tipo de insumo en el inventario.'
                )

            return redirect('inventario')

    else:
        form = AgregarBultosForm()

    return render(
        request,
        'agregar_bultos.html',
        {'form': form}
    )



# GASTOS OPERATIVOS ANDRES

def formato_numero(valor):
    if valor is None:
        return "0"
    try:
        return "{:,.0f}".format(float(valor)).replace(",", ".")
    except (ValueError, TypeError):
        return "0"

@login_required
def registrar_gasto(request):
    form = GastoOperativoForm()
    error_manual = None

    if request.method == 'POST':
        form = GastoOperativoForm(request.POST)

        categoria = request.POST.get('categoria', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        monto = request.POST.get('monto', '')

        if not categoria:
            error_manual = "Debes seleccionar una categoría."
        elif not descripcion:
            error_manual = "La descripción es obligatoria."
        elif not monto:
            error_manual = "El monto es obligatorio."
        else:
            try:
                # AQUI ESTA LA MAGIA: Limpiamos los puntos de miles antes de convertir a número
                monto_limpio = str(monto).replace('.', '').replace(',', '.')
                monto_float = float(monto_limpio)
                if monto_float <= 0:
                    error_manual = "El monto debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "El monto debe ser un número válido."

        if error_manual is None:
            gasto = GastoOperativo(
                categoria=categoria,
                descripcion=descripcion,
                monto=monto_float,
                registrado_por=request.user,
            )
            gasto.save()
            monto_bonito = formato_numero(gasto.monto)
            messages.success(request, f'Gasto registrado. Monto: ${monto_bonito}')
            return redirect('registrar_gasto')

    hoy = date.today()
    gastos_mes = GastoOperativo.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).aggregate(total=Sum('monto'))['total'] or 0

    gastos_totales = GastoOperativo.objects.aggregate(
        total=Sum('monto')
    )['total'] or 0

    costo_alimento_mes = Alimento.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).aggregate(total=Sum('costo_total'))['total'] or 0

    cubetas_producidas = RegistroProduccion.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).aggregate(total=Sum('cantidad_cubetas'))['total'] or 0

    costo_total_mes = gastos_mes + costo_alimento_mes
    if cubetas_producidas > 0:
        costo_por_cubeta = costo_total_mes / cubetas_producidas
    else:
        costo_por_cubeta = 0

    # --- PAGINACIÓN ---
    gastos_list = GastoOperativo.objects.all().order_by('-fecha')
    paginator = Paginator(gastos_list, 5)
    page_number = request.GET.get('page')
    gastos = paginator.get_page(page_number)

    for gasto in gastos:
        gasto.monto_form = formato_numero(gasto.monto)    

    gastos_mes_form = formato_numero(gastos_mes)
    gastos_totales_form = formato_numero(gastos_totales)

    return render(request, 'gasto.html', {
        'form': form,
        'gastos': gastos,
        'error_manual': error_manual,
        'gastos_mes': gastos_mes_form,
        'gastos_totales': gastos_totales_form,
        'costo_alimento_mes': costo_alimento_mes,
        'cubetas_producidas': cubetas_producidas,
        'costo_total_mes': costo_total_mes,
        'costo_por_cubeta': costo_por_cubeta,
    })

@login_required
def editar_gasto(request, pk):
    gasto = get_object_or_404(GastoOperativo, pk=pk)
    error_manual = None

    if request.method == 'POST':
        categoria = request.POST.get('categoria', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        monto = request.POST.get('monto', '')

        if not categoria:
            error_manual = "Debes seleccionar una categoría."
        elif not descripcion:
            error_manual = "La descripción es obligatoria."
        elif not monto:
            error_manual = "El monto es obligatorio."
        else:
            try:
                monto_float = float(monto)
                if monto_float <= 0:
                    error_manual = "El monto debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "El monto debe ser un número válido."

        if error_manual is None:
            gasto.categoria = categoria
            gasto.descripcion = descripcion
            gasto.monto = monto_float
            gasto.save()
            messages.success(request, 'Gasto actualizado correctamente.')
            return redirect('registrar_gasto')
        else:
            form = GastoOperativoForm(request.POST, instance=gasto)
    else:
        form = GastoOperativoForm(instance=gasto)

    gasto.monto_form = f"{int(gasto.monto):,}".replace(",", ".")

    return render(request, 'gasto_editar.html', {
        'form': form,
        'gasto': gasto,
        'error_manual': error_manual,
    })


@login_required
def eliminar_gasto(request, pk):
    gasto = get_object_or_404(GastoOperativo, pk=pk)

    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto eliminado.')
        return redirect('registrar_gasto')

    gasto.monto_form = f"{int(gasto.monto):,}".replace(",", ".")

    return render(request, 'gasto_eliminar.html', {'gasto': gasto})

#JOHAN descargar reporte EXCEL
@login_required
def descargar_reporte_excel(request):
    # Año del reporte: el actual, o ?anio=2025 en la URL
    try:
        anio = int(request.GET.get('anio', date.today().year))
    except ValueError:
        anio = date.today().year
 
    def por_mes(queryset, campo):
        datos = (queryset.filter(fecha__year=anio)
                 .annotate(mes=ExtractMonth('fecha'))
                 .values('mes')
                 .annotate(suma=Sum(campo)))
        return {d['mes']: d['suma'] or 0 for d in datos}
 
    ventas_mes = por_mes(Venta.objects, 'total')
    gastos_mes = por_mes(GastoOperativo.objects, 'monto')
    huevos_mes = por_mes(RegistroProduccion.objects, 'cantidad_huevos')
 
    # Bultos de alimento por mes (columnas "Compra" y "Consumo").
    # Ajusta el nombre del modelo y el campo según lo que usó tu compañero:
    #   compra_bultos = por_mes(IngresoAlimento.objects, 'cantidad_bultos')
    #   consumo_bultos = por_mes(ConsumoAlimento.objects, 'cantidad_bultos')
    # Bultos comprados y consumidos por mes
    compra_bultos = por_mes(Alimento.objects, 'cantidad_bultos')
    consumo_bultos = por_mes(RegistroConsumo.objects, 'bultos_consumidos')
 
    producciones = [(r.fecha, r.cantidad_huevos, r.cantidad_huevos_rotos, r.cantidad_cubetas)
                    for r in RegistroProduccion.objects.filter(fecha__year=anio).order_by('fecha')]
    ventas = [(v.fecha, v.cliente.nombre, v.cantidad_cubetas, float(v.precio_unitario), float(v.total))
              for v in Venta.objects.filter(fecha__year=anio).select_related('cliente').order_by('fecha')]
    gastos = [(g.fecha, g.get_categoria_display(), g.descripcion, float(g.monto))
              for g in GastoOperativo.objects.filter(fecha__year=anio).order_by('fecha')]
 
    contenido = construir_reporte(anio, ventas_mes, gastos_mes, huevos_mes,
                                  producciones, ventas, gastos,
                                  compra_bultos, consumo_bultos)
 
    respuesta = HttpResponse(
        contenido,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    respuesta['Content-Disposition'] = f'attachment; filename="reporte_galpon_{anio}.xlsx"'
    return respuesta

#JOHAN CLIENTES
@login_required
def registrar_cliente(request):
    error_manual = None
 
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
 
        if not nombre:
            error_manual = "El nombre del cliente es obligatorio."
        elif Cliente.objects.filter(nombre__iexact=nombre).exists():
            error_manual = "Ese cliente ya está registrado."
        else:
            Cliente.objects.create(nombre=nombre, telefono=telefono)
            messages.success(request, 'Cliente registrado correctamente.')
            return redirect('registrar_cliente')
 
    return render(request, 'cliente.html', {
        'clientes': Cliente.objects.all(),
        'error_manual': error_manual,
    })

@login_required
@require_POST
def crear_cliente_rapido(request):
    nombre = request.POST.get('nombre', '').strip()
    telefono = request.POST.get('telefono', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre del cliente es obligatorio.'}, status=400)
    if len(nombre) > 100:
        return JsonResponse({'ok': False, 'error': 'El nombre no puede pasar de 100 caracteres.'}, status=400)
    if len(telefono) > 20:
        return JsonResponse({'ok': False, 'error': 'El teléfono no puede pasar de 20 caracteres.'}, status=400)

    existente = Cliente.objects.filter(nombre__iexact=nombre).first()
    if existente:
        return JsonResponse({'ok': True, 'id': existente.id, 'nombre': existente.nombre, 'ya_existia': True})

    cliente = Cliente.objects.create(nombre=nombre, telefono=telefono)
    return JsonResponse({'ok': True, 'id': cliente.id, 'nombre': cliente.nombre, 'ya_existia': False})

# VACUNACIÓN (JEFFRY - HU-005)
@login_required
def vacunacion_lista(request):
    registros = RegistroVacunacion.objects.select_related('lote', 'registrado_por').all()
    
    # NUEVO: Calcular totales globales de inventario
    from .models import Lote
    lotes = Lote.objects.all()
    total_inicial_global = sum(lote.cantidad_inicial for lote in lotes)
    total_actual_global = sum(lote.aves_vivas for lote in lotes)
    
    # NUEVO: Calcular total de dosis aplicadas
    total_vacunadas_global = registros.aggregate(Sum('gallinas_vacunadas'))['gallinas_vacunadas__sum'] or 0
    
    # NUEVO: Calcular cuántas faltan por vacunar
    gallinas_sin_vacunar = max(0, total_actual_global - total_vacunadas_global)

    return render(request, 'vacunacion.html', {
        'registros': registros,
        'total_inicial_global': total_inicial_global,
        'total_actual_global': total_actual_global,
        'total_vacunadas_global': total_vacunadas_global,
        'gallinas_sin_vacunar': gallinas_sin_vacunar,
    })

@login_required
def vacunacion_registrar(request):
    if request.method == 'POST':
        form = RegistroVacunacionForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            
            # ✅ CRITERIO 3: Mostrar advertencia si es parcial
            if hasattr(form, 'add_warning'):
                messages.warning(request, form.add_warning)
            
            registro.save()
            
            # ✅ CRITERIO 2: Alerta de refuerzo (simulada en el mensaje)
            if registro.requiere_refuerzo:
                messages.info(request, f"Se ha agendado un refuerzo para el {registro.fecha_proximo_refuerzo}.")
                
            # ✅ CRITERIO 1: Mensaje de éxito
            messages.success(request, 'Registro de vacunación guardado exitosamente.')
            return redirect('vacunacion_lista')
    else:
        form = RegistroVacunacionForm(initial={'fecha_aplicacion': timezone.localdate()})

    return render(request, 'vacunacion_registrar.html', {'form': form})


@login_required
def vacunacion_editar(request, pk):
    registro = get_object_or_404(RegistroVacunacion, pk=pk)
    
    if request.method == 'POST':
        form = RegistroVacunacionForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro de vacunación actualizado correctamente.')
            return redirect('vacunacion_lista')
    else:
        form = RegistroVacunacionForm(instance=registro)

    
    return render(request, 'vacunacion_editar.html', {'form': form, 'registro': registro})


@login_required
def vacunacion_eliminar(request, pk):
    registro = get_object_or_404(RegistroVacunacion, pk=pk)
    
    if request.method == 'POST':
        registro.delete()
        messages.success(request, 'Registro de vacunación eliminado.')
        return redirect('vacunacion_lista')

    
    return render(request, 'vacunacion_eliminar.html', {'registro': registro})

@login_required
def reporte_rentabilidad(request):
    # Valores por defecto para el formulario
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    context = {
        'fecha_inicio': fecha_inicio_str or inicio_mes.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin_str or hoy.strftime('%Y-%m-%d'),
        'generado': False,
        'error_fechas': None,
    }

    if fecha_inicio_str and fecha_fin_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

            # ✅ CRITERIO 3: Validación de fechas
            if fecha_inicio > fecha_fin:
                context['error_fechas'] = "La fecha inicial no puede ser posterior a la fecha final."
            else:
                context['generado'] = True
                
                # 1. Costos de Alimento (Insumos)
                costo_alimento = Alimento.objects.filter(
                    fecha__range=[fecha_inicio, fecha_fin]
                ).aggregate(total=Sum('costo_total'))['total'] or 0
                
                # 2. Costos de Gastos Operativos
                costo_gastos = GastoOperativo.objects.filter(
                    fecha__range=[fecha_inicio, fecha_fin]
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                # 3. Dosis de Vacunas
                dosis_vacunas = RegistroVacunacion.objects.filter(
                    fecha_aplicacion__range=[fecha_inicio, fecha_fin]
                ).aggregate(total=Sum('gallinas_vacunadas'))['total'] or 0
                
                total_insumos = costo_alimento + costo_gastos

                # 4. Ingresos por Ventas (Huevos)
                ingresos_ventas = Venta.objects.filter(
                    fecha__range=[fecha_inicio, fecha_fin]
                ).aggregate(total=Sum('total'))['total'] or 0
                
                # 5. Producción total de huevos en el periodo
                produccion_huevos = RegistroProduccion.objects.filter(
                    fecha__range=[fecha_inicio, fecha_fin]
                ).aggregate(total=Sum('cantidad_huevos'))['total'] or 0

                # ✅ CRITERIO 2: Cálculo del margen
                margen = ingresos_ventas - total_insumos
                es_rentable = margen >= 0

                # Actualizamos el contexto con los resultados y formateamos los números
                context.update({
                    'costo_alimento': f"{int(costo_alimento):,}".replace(",", "."),
                    'costo_gastos': f"{int(costo_gastos):,}".replace(",", "."),
                    'dosis_vacunas': dosis_vacunas,
                    'total_insumos': f"{int(total_insumos):,}".replace(",", "."),
                    'ingresos_ventas': f"{int(ingresos_ventas):,}".replace(",", "."),
                    'produccion_huevos': produccion_huevos,
                    'margen': f"{int(margen):,}".replace(",", "."),
                    'es_rentable': es_rentable,
                    'fecha_inicio': fecha_inicio_str,
                    'fecha_fin': fecha_fin_str,
                })
        except ValueError:
            context['error_fechas'] = "Formato de fecha inválido."

    return render(request, 'reporte_rentabilidad.html', context)
