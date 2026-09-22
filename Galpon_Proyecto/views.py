from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistroConsumoForm

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

    @login_required
def mortalidad_registrar(request):
    if request.method == 'POST':
        form = RegistroMortalidadForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            registro.save()
            messages.success(request, 'Registro de mortalidad guardado correctamente.')
            return redirect('accounts:mortalidad_lista')
    else:
        form = RegistroMortalidadForm()

    return render(request, 'registrar.html', {'form': form})


    @login_required
def mortalidad_eliminar(request, pk):
    registro = get_object_or_404(RegistroMortalidad, pk=pk)
    registro.delete()
    messages.success(request, 'Registro eliminado.')
    return redirect('accounts:mortalidad_lista')