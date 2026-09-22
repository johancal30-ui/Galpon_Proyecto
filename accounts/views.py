from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

from django.contrib.auth.views import (PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView,)
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from .models import RegistroMortalidad
from .forms import RegistroMortalidadForm



def login_view(request):
    # Si el usuario ya está logueado, lo mandamos a la home
    if request.user.is_authenticated:
        return redirect('accounts:home')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('accounts:home')
        else:
            error = "Usuario o contraseña incorrectos."

    return render(request, 'login.html', {'error': error})

def registro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()

    return render(request, 'registro.html', {'form': form})

def cierre(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def home_view(request):
    return render(request, 'home.html')

class password_reset_view(PasswordResetView):
    template_name = 'recuperar.html'
    email_template_name = 'recuperar_correo.html'
    success_url = '/recuperar/enviado/'

class password_reset_done_view(PasswordResetDoneView):
    template_name = 'recuperar_enviado.html'

class password_reset_confirm_view(PasswordResetConfirmView):
    template_name = 'recuperar_confirmar.html'
    success_url = '/recuperar/completado/'

class password_reset_complete_view(PasswordResetCompleteView):
    template_name = 'recuperar_completado.html'


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