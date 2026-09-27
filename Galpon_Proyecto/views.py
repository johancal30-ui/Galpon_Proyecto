from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import RegistroProduccion, RegistroConsumo, RegistroMortalidad
from .forms import RegistroConsumoForm, RegistroMortalidadForm


# ==========================================
# PRODUCCIÓN (JOHAN)
# ==========================================
def registrar_produccion(request):
    if request.method == 'POST':
        huevos = request.POST.get('cantidad_huevos')
        cubetas = request.POST.get('cantidad_cubetas')
        if not huevos or not cubetas:
            messages.error(request, "Por favor, complete todos los campos.")
        else:
            try:
                huevos = int(huevos)
                cubetas = int(cubetas)
                if huevos <= 0 or cubetas <= 0:
                    messages.error(request, "La cantidad debe ser un número entero mayor a cero")
                else:
                    RegistroProduccion.objects.create(
                        cantidad_huevos=huevos,
                        cantidad_cubetas=cubetas
                    )
                    messages.success(request, "Registro actualizado exitosamente")
                    return redirect('registrar_produccion')
            except (ValueError, TypeError):
                messages.error(request, "La cantidad debe ser un número entero mayor a cero")

    registros = RegistroProduccion.objects.all()
    return render(request, 'produccion.html', {'registros': registros})


# ==========================================
# CONSUMO (JHON)
# ==========================================
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


# ==========================================
# MORTALIDAD (JEFFRY)
# ==========================================
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