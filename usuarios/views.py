from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import  EmailLoginForm
from .forms import UserForm, PerfilForm, RecuperarContrasenaForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings

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

#Vista para recuperar contraseña
User = get_user_model()

def recuperar_contrasena(request):
    if request.method == 'POST':
        form = RecuperarContrasenaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generar una contraseña aleatoria de 8 caracteres
                nueva_contrasena = get_random_string(length=8)
                user.set_password(nueva_contrasena)
                user.save()

                # Enviar el correo electrónico con la nueva contraseña
                send_mail(
                    'Recuperación de contraseña - Alquileres María',
                    f'Hola {user.username}, tu nueva contraseña es: {nueva_contrasena}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                messages.success(request, 'Se ha enviado una nueva contraseña a tu correo.')
                return redirect('usuarios:login')
            except User.DoesNotExist:
                messages.error(request, 'No se encontró ninguna cuenta con ese correo.',extra_tags='danger')
                return redirect('usuarios:recuperar_contrasena')
    else:
        form = RecuperarContrasenaForm()

    return render(request, 'usuarios/recuperar_contrasena.html', {'form': form})