from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import date
from datetime import datetime
from .models import (RegistroProduccion, RegistroConsumo, RegistroMortalidad,Venta, Alimento, Inventario, AlertaStock, GastoOperativo)
from .forms import (RegistroConsumoForm, RegistroMortalidadForm,VentaForm, AlimentoForm, InventarioForm, GastoOperativoForm)
#creado por johan para descargar reporte excel:
from datetime import date
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from .reportes import construir_reporte
# creado por johan para CLIENTESS
from .models import Cliente


# PRODUCCIÓN (JOHAN)
def registrar_produccion(request):
    if request.method == 'POST':
        huevos = request.POST.get('cantidad_huevos')
        cubetas = request.POST.get('cantidad_cubetas')
        rotos = request.POST.get('cantidad_huevos_rotos') or '0'
        fecha_texto = request.POST.get('fecha')                      

        if not huevos or not cubetas or not fecha_texto:             #fecha_texto
            messages.error(request, "Por favor, complete todos los campos.")
        else:
            # convertir y validar la fecha
            try:
                fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
            except ValueError:
                fecha = None

            if fecha is None:                                        #
                messages.error(request, "La fecha no es válida")
            elif fecha > timezone.localdate():                       
                messages.error(request, "La fecha no puede ser futura")
            else:
                try:
                    huevos = int(huevos)
                    cubetas = int(cubetas)
                    rotos = int(rotos)
                    if huevos <= 0 or cubetas <= 0:
                        messages.error(request, "La cantidad debe ser un número entero mayor a cero")
                    elif rotos < 0:
                        messages.error(request, "Los huevos rotos deben ser un número entero mayor o igual a cero")
                    elif rotos > huevos:
                        messages.error(request, "Los huevos rotos no pueden superar el total recolectado")
                    else:
                        RegistroProduccion.objects.create(
                            fecha=fecha,                             
                            cantidad_huevos=huevos,
                            cantidad_huevos_rotos=rotos,
                            cantidad_cubetas=cubetas
                        )
                        messages.success(request, "Registro guardado exitosamente")
                        return redirect('registrar_produccion')
                except (ValueError, TypeError):
                    messages.error(request, "La cantidad debe ser un número entero mayor a cero")

    registros = RegistroProduccion.objects.all()
    return render(request, 'produccion.html', {
        'registros': registros,
        'hoy': timezone.localdate(),                                 
    })


def editar_produccion(request, pk):
    registro = get_object_or_404(RegistroProduccion, pk=pk)
    if request.method == 'POST':
        huevos = request.POST.get('cantidad_huevos')
        cubetas = request.POST.get('cantidad_cubetas')
        rotos = request.POST.get('cantidad_huevos_rotos') or '0'
        fecha_texto = request.POST.get('fecha')                      

        # convertir y validar la fecha
        try:
            fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            fecha = None

        if fecha is None:                                            
            messages.error(request, "La fecha no es válida")
        elif fecha > timezone.localdate():                          
            messages.error(request, "La fecha no puede ser futura")
        else:
            try:
                huevos = int(huevos)
                cubetas = int(cubetas)
                rotos = int(rotos)
                if huevos <= 0 or cubetas <= 0:
                    messages.error(request, "La cantidad debe ser un número entero mayor a cero")
                elif rotos < 0:
                    messages.error(request, "Los huevos rotos deben ser un número entero mayor o igual a cero")
                elif rotos > huevos:
                    messages.error(request, "Los huevos rotos no pueden superar el total recolectado")
                else:
                    registro.fecha = fecha                           # NUEVO
                    registro.cantidad_huevos = huevos
                    registro.cantidad_huevos_rotos = rotos
                    registro.cantidad_cubetas = cubetas
                    registro.save()
                    messages.success(request, "Registro actualizado exitosamente")
                    return redirect('registrar_produccion')
            except (ValueError, TypeError):
                messages.error(request, "La cantidad debe ser un número entero mayor a cero")

    return render(request, 'produccion_editar.html', {'registro': registro})
def eliminar_produccion(request, pk):
    registro = get_object_or_404(RegistroProduccion, pk=pk)

    if request.method == 'POST':
        registro.delete()
        messages.success(request, "Registro eliminado exitosamente")
        return redirect('registrar_produccion')

    return render(request, 'produccion_eliminar.html', {'registro': registro})
# CONSUMO (JHON)
def registrar_consumo(request):
    if request.method == 'POST':
        form = RegistroConsumoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)

            if registro.es_consumo_anomalo:
                messages.warning(
                    request,
                    f"Advertencia: Consumo anómalo ({registro.consumo_gramos_por_ave} g/ave/día) "
                    f"para {registro.poblacion_gallinas} gallinas. "
                    f"Verifique un posible desperdicio o problema de nutrición."
                )

            registro.save()
            messages.success(request, f"Registro guardado. Índice: {registro.consumo_gramos_por_ave} g/ave/día.")
            return redirect('registrar_consumo')
    else:
        form = RegistroConsumoForm()

    return render(request, 'consumo_form.html', {'form': form})



# MORTALIDAD (JEFFRY)
@login_required
def mortalidad_lista(request):
    registros = RegistroMortalidad.objects.select_related('lote', 'registrado_por').all()
    total_cantidad = registros.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    lotes_afectados = registros.values('lote').distinct().count()
    
    # NUEVO: Contador exacto para el template
    total_registros = registros.count() 

    return render(request, 'mortalidad.html', {
        'registros': registros,
        'total_cantidad': total_cantidad,
        'lotes_afectados': lotes_afectados,
        'total_registros': total_registros, # <-- Enviamos el dato
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
        form = RegistroMortalidadForm()

    return render(request, 'registrar.html', {'form': form})


@login_required
def mortalidad_eliminar(request, pk):
    registro = get_object_or_404(RegistroMortalidad, pk=pk)
    registro.delete()
    messages.success(request, 'Registro eliminado.')
    return redirect('mortalidad_lista')


# VENTAS (ANDRÉS)

@login_required
def registrar_venta(request):
    form = VentaForm()
    error_manual = None

    if request.method == 'POST':
        form = VentaForm(request.POST)

        cliente = request.POST.get('cliente', '').strip()
        cantidad = request.POST.get('cantidad_cubetas', '')
        precio = request.POST.get('precio_unitario', '')

        # Validar cliente
        if not cliente:
            error_manual = "El nombre del cliente es obligatorio."

        # Validar cantidad
        elif not cantidad:
            error_manual = "La cantidad de cubetas es obligatoria."
        else:
            try:
                cantidad_int = int(cantidad)
                if cantidad_int <= 0:
                    error_manual = "La cantidad debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "La cantidad debe ser un número entero."

        # Validar precio
        if error_manual is None:
            if not precio:
                error_manual = "El precio por cubeta es obligatorio."
            else:
                try:
                    precio_limpio = str(precio).replace(".", "").replace(",", ".")
                    precio_float = float(precio_limpio)
                    if precio_float <= 0:
                        error_manual = "El precio debe ser mayor a cero."
                except (ValueError, TypeError):
                    error_manual = "El precio debe ser un número válido."

        # Verificar stock disponible
        if error_manual is None:
            total_producido = RegistroProduccion.objects.aggregate(
                total=Sum('cantidad_cubetas')
            )['total'] or 0

            total_vendido = Venta.objects.aggregate(
                total=Sum('cantidad_cubetas')
            )['total'] or 0

            stock_disponible = total_producido - total_vendido

            if cantidad_int > stock_disponible:
                error_manual = f"Stock insuficiente. Solo hay {stock_disponible} cubetas disponibles."

        # Si todo está bien, guardar
        if error_manual is None:
            venta = Venta(
                cliente=cliente,
                cantidad_cubetas=cantidad_int,
                precio_unitario=precio_float,
                cantidad_huevos=cantidad_int * 30,
                total=cantidad_int * precio_float,
                registrado_por=request.user,
            )
            venta.save()
            messages.success(request, f'Venta registrada. Total: ${venta.total}')
            return redirect('registrar_venta')

    total_producido = RegistroProduccion.objects.aggregate(
        total=Sum('cantidad_cubetas')
    )['total'] or 0
    total_vendido = Venta.objects.aggregate(
        total=Sum('cantidad_cubetas')
    )['total'] or 0
    stock_disponible = total_producido - total_vendido

    hoy = timezone.now().date()
    ingresos_hoy = Venta.objects.filter(fecha=hoy).aggregate(
        total=Sum('total')
    )['total'] or 0

    ventas = Venta.objects.all()

    ingresos_hoy = f"{int(ingresos_hoy):,}".replace(",", ".")
    for v in ventas:
        v.total_form = f"{int(v.total):,}".replace(",", ".")
        v.precio_form = f"{int(v.precio_unitario):,}".replace(",", ".")

    return render(request, 'venta.html', {
        'form': form,
        'ventas': ventas,
        'error_manual': error_manual,
        'stock_disponible': stock_disponible,
        'ingresos_hoy': ingresos_hoy,
    })

@login_required
def editar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    error_manual = None

    if request.method == 'POST':
        cliente = request.POST.get('cliente', '').strip()
        cantidad = request.POST.get('cantidad_cubetas', '')
        precio = request.POST.get('precio_unitario', '')

        if not cliente:
            error_manual = "El nombre del cliente es obligatorio."
        elif not cantidad:
            error_manual = "La cantidad de cubetas es obligatoria."
        else:
            try:
                cantidad_int = int(cantidad)
                if cantidad_int <= 0:
                    error_manual = "La cantidad debe ser mayor a cero."
            except (ValueError, TypeError):
                error_manual = "La cantidad debe ser un número entero."

        if error_manual is None:
            if not precio:
                error_manual = "El precio por cubeta es obligatorio."
            else:
                try:
                    precio_limpio = str(precio).replace(".", "").replace(",", ".")
                    precio_float = float(precio_limpio)
                    if precio_float <= 0:
                        error_manual = "El precio debe ser mayor a cero."
                except (ValueError, TypeError):
                    error_manual = "El precio debe ser un número válido."

        if error_manual is None:
            venta.cliente = cliente
            venta.cantidad_cubetas = cantidad_int
            venta.precio_unitario = precio_float
            venta.cantidad_huevos = cantidad_int * 30
            venta.total = cantidad_int * precio_float
            venta.save()
            messages.success(request, 'Venta actualizada correctamente.')
            return redirect('registrar_venta')
        else:
            # Si hay error, volvemos a mostrar el form con los datos actuales
            form = VentaForm(request.POST, instance=venta)
    else:
        form = VentaForm(instance=venta)

    venta.precio_form = f"{int(venta.precio_unitario):,}".replace(",", ".")

    return render(request, 'venta_editar.html', {
        'form': form,
        'venta': venta,
        'error_manual': error_manual,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.delete()
        messages.success(request, 'Venta eliminada.')
        return redirect('registrar_venta')

    venta.total_form = f"{int(venta.total):,}".replace(",", ".")

    return render(request, 'venta_eliminar.html', {'venta': venta})


#(ALIMENTO ANDRRES)

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

        # Validar kilos por bulto
        if error_manual is None:
            if not kilos:
                error_manual = "Los kilos por bulto son obligatorios."
            else:
                try:
                    kilos_float = float(kilos)
                    if kilos_float <= 0:
                        error_manual = "Los kilos por bulto deben ser mayores a cero."
                except (ValueError, TypeError):
                    error_manual = "Los kilos deben ser un número válido."

        # Validar costo unitario
        if error_manual is None:
            if not costo:
                error_manual = "El costo unitario es obligatorio."
            else:
                try:
                    costo_float = float(costo)
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
            messages.success(request, f'Ingreso registrado. Costo total: ${alimento.costo_total}')
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

    # Historial completo
    historial = Alimento.objects.all()

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
        total_invertido = f"{int(total_invertido):,}".replace(",", ".")
    
    for a in historial:
        a.costo_unit_form = f"{int(a.costo_unitario):,}".replace(",", ".")
        a.costo_total_form = f"{int(a.costo_total):,}".replace(",", ".")
        
    for s in stock_por_tipo:
        s['costo_total_form'] = f"{int(s['costo_total']):,}".replace(",", ".")

    return render(request, 'alimento.html', {
        'form': form,
        'stock_por_tipo': stock_por_tipo,
        'historial': historial,
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

@login_required
def inventario(request):
    inventarios = Inventario.objects.all()

    if request.method == 'POST':
        form = InventarioForm(request.POST)

        if form.is_valid():
            inventario = form.save()
            inventario.verificar_alerta()

            if inventario.stock_bajo:
                messages.warning(
                    request,
                    f'⚠️ Alerta: el stock de {inventario.get_tipo_display()} '
                    f'está en {inventario.stock_actual}, '
                    f'por debajo o igual al mínimo de {inventario.stock_minimo}.'
                )
            else:
                messages.success(
                    request,
                    f'Inventario de {inventario.get_tipo_display()} actualizado correctamente.'
                )

            return redirect('inventario')
    else:
        form = InventarioForm()

    alertas = AlertaStock.objects.filter(activa=True)

    return render(request, 'inventario.html', {
        'form': form,
        'inventarios': inventarios,
        'alertas': alertas,
    })


# GASTOS OPERATIVOS ANDRES
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
                monto_float = float(monto)
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
            messages.success(request, f'Gasto registrado. Monto: ${gasto.monto}')
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

    gastos = GastoOperativo.objects.all()

    gastos_mes = f"{int(gastos_mes):,}".replace(",", ".")
    gastos_totales = f"{int(gastos_totales):,}".replace(",", ".")

    for gasto in gastos:
        gasto.monto_form = f"{int(gasto.monto):,}".replace(",", ".")    

    return render(request, 'gasto.html', {
        'form': form,
        'gastos': gastos,
        'error_manual': error_manual,
        'gastos_mes': gastos_mes,
        'gastos_totales': gastos_totales,
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
    compra_bultos = {}    # vacío = la columna sale en blanco
    consumo_bultos = {}
 
    producciones = [(r.fecha, r.cantidad_huevos, r.cantidad_huevos_rotos, r.cantidad_cubetas)
                    for r in RegistroProduccion.objects.filter(fecha__year=anio).order_by('fecha')]
    ventas = [(v.fecha, v.cliente, v.cantidad_cubetas, float(v.precio_unitario), float(v.total))
              for v in Venta.objects.filter(fecha__year=anio).order_by('fecha')]
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