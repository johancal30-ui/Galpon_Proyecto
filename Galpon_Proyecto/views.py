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
