from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages


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