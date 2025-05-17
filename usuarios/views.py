from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import  EmailLoginForm
from .forms import UserForm, PerfilForm
from django.contrib.auth.views import LoginView, LogoutView

def registro(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        perfil_form = PerfilForm(request.POST)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            perfil = perfil_form.save(commit=False)
            perfil.usuario = user   # Asignar el usuario al perfil
            perfil.save()
            messages.success(request, f"¡Cuenta creada exitosamente! Bienvenido/a, {user.username}. Utiliza tus credenciales para autenticarte")
            return redirect('home')
    else:
        user_form = UserForm()
        perfil_form = PerfilForm()
        
    return render(request, 'usuarios/registro.html', {'user_form': user_form, 'perfil_form': perfil_form})

def iniciar_sesion(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"¡Bienvenido/a, {user.username}!")
                return redirect('home')
            else:
                messages.error(request, "Correo o contraseña incorrectos.")
        else:
            messages.error(request, "Formulario no válido.")
    else:
        form = EmailLoginForm()
    return render(request, 'usuarios/login.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Sesión cerrada exitosamente.")
    return redirect('home')


@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html')