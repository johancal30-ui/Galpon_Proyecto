from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import RegistroProduccion
from .models import RegistroConsumo
from .forms import RegistroConsumoForm

#JOHAN
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
                        cantidad_huevos = huevos,
                        cantidad_cubetas = cubetas
                    )
                    messages.success(request, "Registro actualizado exitosamente")
                    return redirect('registrar_produccion')
            except (ValueError, TypeError):
                messages.error(request, "La cantidad debe ser un número entero mayor a cero")

    registros = RegistroProduccion.objects.all()
    return render(request, 'produccion_editar.html', {'registro': registro})


#JHON
def registrar_consumo(request):
    if request.method == 'POST':
        form = RegistroConsumoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            
            # Validar anomalía para mostrar advertencia
            if registro.es_consumo_anomalo:
                messages.warning(
                    request, 
                    f"Advertencia: Consumo anómalo ({registro.consumo_gramos_por_ave} g/ave/día) para {registro.poblacion_gallinas} gallinas. Verifique un posible desperdicio o problema de nutrición."
                )
            
            registro.save()
            messages.success(request, f"Registro guardado . Índice: {registro.consumo_gramos_por_ave} g/ave/día.")
            return redirect('registrar_consumo')
    else:
        form = RegistroConsumoForm()

    return render(request, 'consumo_form.html', {'form': form})
