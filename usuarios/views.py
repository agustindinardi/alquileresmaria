from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import EmailLoginForm, CodigoValidacionForm, EmpleadoForm
from .forms import UserForm, PerfilForm, RecuperarContrasenaForm
from .models import Empleado
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings
import random
import string

def registro(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        perfil_form = PerfilForm(request.POST)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            perfil = perfil_form.save(commit=False)
            perfil.usuario = user   # Asignar el usuario al perfil
            perfil.save()
            messages.success(request, f"¡Cuenta creada exitosamente! Bienvenido/a, {user.first_name} {user.last_name}. Utiliza tus credenciales para autenticarte")
            return redirect('home')
    else:
        user_form = UserForm()
        perfil_form = PerfilForm()
        
    return render(request, 'usuarios/registro.html', {'user_form': user_form, 'perfil_form': perfil_form})

def generar_codigo_seguridad():
    """Genera un código de seguridad en formato XXXX-X"""
    numeros = ''.join(random.choices(string.digits, k=4))
    letra = random.choice(string.ascii_uppercase)
    return f"{numeros}-{letra}"

def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.email == "alquileresmaria4@gmail.com" or user.is_staff or user.is_superuser

def administrador_requerido(user):
    """Decorador para verificar si el usuario es administrador"""
    return es_administrador(user)

def generar_contrasena_empleado():
    """Genera una contraseña aleatoria de 6 caracteres para empleados"""
    return get_random_string(length=6)

def iniciar_sesion(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                # Verificar si es administrador
                if es_administrador(user):
                    # Generar código de seguridad
                    codigo = generar_codigo_seguridad()
                    
                    # Guardar código y user_id en la sesión
                    request.session['codigo_seguridad'] = codigo
                    request.session['user_id_pendiente'] = user.id
                    # Guardar el backend utilizado
                    request.session['auth_backend'] = user.backend
                    
                    # Enviar código por email
                    try:
                        send_mail(
                            'Código de seguridad - Alquileres María',
                            f'Hola {user.first_name},\n\nTu código de seguridad es: {codigo}\n\nIngresa este código para completar el inicio de sesión.\n\nSi no solicitaste este código, ignora este mensaje.',
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            fail_silently=False,
                        )
                        print("EL CODIGO DE SEGURIDAD ES:", codigo)  # Pa que no rompa las bola
                        # Redirigir sin mensaje - el mensaje se muestra en la página de validación
                        return redirect('usuarios:validar_codigo')
                    except Exception as e:
                        messages.error(request, "Error al enviar el código de seguridad. Intenta nuevamente.")
                        return render(request, 'usuarios/login.html', {'form': form})
                else:
                    # Usuario normal, iniciar sesión directamente
                    login(request, user)
                    messages.success(request, f"¡Bienvenido/a, {user.first_name} {user.last_name}!")
                    return redirect('home')
            # Si la autenticación falla, no agregamos mensaje aquí
            # El formulario ya maneja los errores de autenticación
    else:
        form = EmailLoginForm()
    return render(request, 'usuarios/login.html', {'form': form})

def validar_codigo(request):
    # Verificar que hay una sesión de código pendiente
    if 'codigo_seguridad' not in request.session or 'user_id_pendiente' not in request.session:
        messages.error(request, "No hay ningún código de seguridad pendiente.")
        return redirect('usuarios:login')
    
    # Verificar si es la primera carga (viene desde login)
    primera_carga = request.method == 'GET'
    
    if request.method == 'POST':
        form = CodigoValidacionForm(request.POST)
        if form.is_valid():
            codigo_ingresado = form.cleaned_data.get('codigo')
            codigo_correcto = request.session.get('codigo_seguridad')
            
            if codigo_ingresado == codigo_correcto:
                # Código correcto, iniciar sesión
                try:
                    User = get_user_model()
                    user = User.objects.get(id=request.session['user_id_pendiente'])
                    # Obtener el backend que se usó originalmente
                    backend_path = request.session.get('auth_backend')
                    if backend_path:
                        from django.utils.module_loading import import_string
                        backend = import_string(backend_path)()
                        user.backend = backend_path
                        login(request, user)
                    else:
                        # Fallback a EmailBackend si no se guardó el backend
                        from .backends import EmailBackend
                        backend = EmailBackend()
                        user.backend = 'usuarios.backends.EmailBackend'
                        login(request, user, backend=backend)
                    
                    # Limpiar la sesión
                    del request.session['codigo_seguridad']
                    del request.session['user_id_pendiente']
                    if 'auth_backend' in request.session:
                        del request.session['auth_backend']
                    
                    messages.success(request, f"¡Bienvenido/a, {user.first_name} {user.last_name}!")
                    return redirect('home')
                except User.DoesNotExist:
                    messages.error(request, "Error en la validación. Intenta iniciar sesión nuevamente.")
                    return redirect('usuarios:login')
            else:
                messages.error(request, "El código ingresado es incorrecto.")
    else:
        form = CodigoValidacionForm()
    
    return render(request, 'usuarios/validar_codigo.html', {
        'form': form, 
        'primera_carga': primera_carga
    })

def cerrar_sesion(request):
    logout(request)
    messages.success(request, "Sesión cerrada exitosamente.")
    return redirect('home')

@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html')

# VISTAS DE EMPLEADOS

@login_required
@user_passes_test(administrador_requerido)
def lista_empleados(request):
    """Vista para listar todos los empleados - solo para administradores"""
    empleados = Empleado.objects.filter(activo=True).select_related('usuario')
    return render(request, 'usuarios/lista_empleados.html', {
        'empleados': empleados
    })

@login_required
@user_passes_test(administrador_requerido)
def crear_empleado(request):
    """Vista para crear un nuevo empleado - solo para administradores"""
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            try:
                pswd = generar_contrasena_empleado()
                # Crear usuario
                User = get_user_model()
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=pswd
                )
                
                # Crear empleado
                empleado = form.save(commit=False)
                empleado.usuario = user
                empleado.save()
                
                # Enviar contraseña por correo
                try:
                    send_mail(
                        'Bienvenido a Alquileres María - Credenciales de acceso',
                        f'Hola {user.first_name},\n\n'
                        f'Te damos la bienvenida a Alquileres María. Has sido registrado como empleado.\n\n'
                        f'Tus credenciales de acceso son:\n'
                        f'Email: {user.email}\n'
                        f'Contraseña: {pswd}\n\n'  # Nota: esto enviará el hash, necesitas guardar la contraseña antes del hash
                        f'Por favor, cambia tu contraseña después del primer inicio de sesión.\n\n'
                        f'Saludos,\n'
                        f'Equipo de Alquileres María',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, f'Empleado {user.first_name} {user.last_name} registrado exitosamente. Se ha enviado la contraseña por correo.')
                    return redirect('usuarios:lista_empleados')
                    
                except Exception as e:
                    # Si falla el envío del correo, eliminar el usuario y empleado creados
                    empleado.delete()
                    user.delete()
                    messages.error(request, 'Error al enviar las credenciales por correo. El empleado no fue registrado.')
                    
            except Exception as e:
                messages.error(request, f'Error al crear el empleado: {str(e)}')
                
    else:
        form = EmpleadoForm()
    
    return render(request, 'usuarios/crear_empleado.html', {
        'form': form,
        'titulo': 'Registrar Empleado'
    })

@login_required
@user_passes_test(administrador_requerido)
def editar_empleado(request, empleado_id):
    """Vista para editar un empleado existente - solo para administradores"""
    empleado = get_object_or_404(Empleado, id=empleado_id, activo=True)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado, instance_pk=empleado.pk)
        if form.is_valid():
            try:
                # Actualizar datos del usuario
                user = empleado.usuario
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.email = form.cleaned_data['email']
                user.username = form.cleaned_data['email']
                user.save()
                
                # Actualizar empleado
                form.save()
                
                messages.success(request, f'Empleado {user.first_name} {user.last_name} actualizado exitosamente.')
                return redirect('usuarios:lista_empleados')
                
            except Exception as e:
                messages.error(request, f'Error al actualizar el empleado: {str(e)}')
                
    else:
        form = EmpleadoForm(instance=empleado, instance_pk=empleado.pk)
    
    return render(request, 'usuarios/crear_empleado.html', {
        'form': form,
        'empleado': empleado,
        'titulo': 'Modificar Empleado'
    })

@login_required
@user_passes_test(administrador_requerido)
def eliminar_empleado(request, empleado_id):
    """Vista para eliminar (desactivar) un empleado - solo para administradores"""
    empleado = get_object_or_404(Empleado, id=empleado_id, activo=True)
    
    if request.method == 'POST':
        # Desactivar en lugar de eliminar físicamente
        empleado.activo = False
        empleado.save()
        
        # También desactivar el usuario
        empleado.usuario.is_active = False
        empleado.usuario.save()
        
        messages.success(request, f'Empleado {empleado.usuario.first_name} {empleado.usuario.last_name} eliminado exitosamente.')
        return redirect('usuarios:lista_empleados')
    
    return render(request, 'usuarios/confirmar_eliminar.html', {
        'empleado': empleado
    })

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