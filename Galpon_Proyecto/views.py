from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import RegistroProduccion, RegistroConsumo, RegistroMortalidad, Venta
from .forms import RegistroConsumoForm, RegistroMortalidadForm, VentaForm


# PRODUCCIÓN (JOHAN)
def registrar_produccion(request):
    if request.method == 'POST':
        huevos = request.POST.get('cantidad_huevos')
        cubetas = request.POST.get('cantidad_cubetas')
        rotos = request.POST.get('cantidad_huevos_rotos') or '0'
        if not huevos or not cubetas:
            messages.error(request, "Por favor, complete todos los campos.")
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
                        cantidad_huevos=huevos,
                        cantidad_huevos_rotos=rotos,
                        cantidad_cubetas=cubetas
                    )
                    messages.success(request, "Registro guardado exitosamente")
                    return redirect('registrar_produccion')
            except (ValueError, TypeError):
                messages.error(request, "La cantidad debe ser un número entero mayor a cero")

    registros = RegistroProduccion.objects.all()
    return render(request, 'produccion.html', {'registros': registros})


def editar_produccion(request, pk):
    registro = get_object_or_404(RegistroProduccion, pk=pk)
    if request.method == 'POST':
        huevos = request.POST.get('cantidad_huevos')
        cubetas = request.POST.get('cantidad_cubetas')
        rotos = request.POST.get('cantidad_huevos_rotos') or '0'
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
    registros = RegistroMortalidad.objects.select_related('lote').all()
    total_cantidad = registros.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    lotes_afectados = registros.values('lote').distinct().count()

    return render(request, 'mortalidad.html', {
        'registros': registros,
        'total_cantidad': total_cantidad,
        'lotes_afectados': lotes_afectados,
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
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.registrado_por = request.user
            venta.cantidad_huevos = venta.cantidad_cubetas * 30  # <-- Calcular aquí
            venta.save()
            messages.success(request, f'Venta registrada. Total: ${venta.total}')
            return redirect('registrar_venta')
    else:
        form = VentaForm()

    ventas = Venta.objects.all()
    return render(request, 'venta.html', {'form': form, 'ventas': ventas})


@login_required
def editar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada correctamente.')
            return redirect('registrar_venta')
    else:
        form = VentaForm(instance=venta)

    return render(request, 'venta_editar.html', {'form': form, 'venta': venta})


@login_required
def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.delete()
        messages.success(request, 'Venta eliminada.')
        return redirect('registrar_venta')

    return render(request, 'venta_eliminar.html', {'venta': venta})