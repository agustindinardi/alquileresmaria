from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import EmailLoginForm, CodigoValidacionForm, EmpleadoForm, ClientePorEmpleadoForm
from .forms import UserForm, PerfilForm, RecuperarContrasenaForm
from .models import Empleado
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings
from django.db import transaction
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

def es_empleado(user):
    return hasattr(user, 'empleado')

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
    if request.method == "POST":
        empleado_id = request.POST.get("empleado_id")
        empleado = get_object_or_404(Empleado, id=empleado_id, activo=True)

        # Dar de baja
        empleado.activo = False
        empleado.save()
        empleado.usuario.is_active = False
        empleado.usuario.save()

        messages.success(request, f"Empleado {empleado.usuario.first_name} {empleado.usuario.last_name} dado de baja correctamente.")
        return redirect('usuarios:lista_empleados')

    empleados = Empleado.objects.filter(activo=True)
    return render(request, 'usuarios/lista_empleados.html', {'empleados': empleados})


@login_required
@user_passes_test(administrador_requerido)
def crear_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            dni = form.cleaned_data['dni']
            sucursal = form.cleaned_data['sucursal']  # Obtener la sucursal
            User = get_user_model()
            pswd = generar_contrasena_empleado()

            try:
                user_existente = User.objects.filter(email=email).first()

                if user_existente:
                    # Buscar empleado asociado al usuario
                    empleado_existente = Empleado.objects.filter(usuario=user_existente).first()

                    if empleado_existente:
                        if empleado_existente.activo:
                            messages.error(request, 'Ya existe un usuario activo con ese correo.')
                            return redirect('usuarios:crear_empleado')
                        else:
                            # Reactivar empleado y usuario
                            user_existente.first_name = form.cleaned_data['first_name']
                            user_existente.last_name = form.cleaned_data['last_name']
                            user_existente.username = email
                            user_existente.is_active = True
                            user_existente.set_password(pswd)
                            user_existente.save()

                            empleado_existente.dni = dni
                            empleado_existente.fecha_nacimiento = form.cleaned_data['fecha_nacimiento']
                            empleado_existente.sucursal = sucursal
                            empleado_existente.activo = True
                            empleado_existente.save()

                            send_mail(
                                'Empleado reactivado - Alquileres María',
                                f'Hola {user_existente.first_name},\n\n'
                                f'Tu cuenta fue reactivada. Tus nuevas credenciales son:\n'
                                f'Email: {email}\n'
                                f'Contraseña: {pswd}\n'
                                f'Sucursal asignada: {sucursal}\n\n'
                                f'Por favor, inicia sesión con estas credenciales.\n\n'
                                f'Saludos,\n'
                                f'Administración - Alquileres María',
                                settings.DEFAULT_FROM_EMAIL,
                                [email],
                                fail_silently=False,
                            )

                            messages.success(request, f'Empleado {user_existente.first_name} reactivado con éxito.')
                            return redirect('usuarios:lista_empleados')
                    else:
                        messages.error(request, 'Ese email ya está en uso por un usuario sin relación con un empleado.')
                        return redirect('usuarios:crear_empleado')

                # Si no existe usuario, creamos todo nuevo
                nuevo_user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=pswd
                )
                empleado = form.save(commit=False)
                empleado.usuario = nuevo_user
                empleado.save()

                send_mail(
                    'Credenciales de acceso - Alquileres María',
                    f'Hola {nuevo_user.first_name},\n\n'
                    f'¡Bienvenido/a al equipo de Alquileres María!\n\n'
                    f'Tu cuenta fue creada exitosamente. Aquí tienes tus credenciales de acceso:\n\n'
                    f'Email: {email}\n'
                    f'Contraseña: {pswd}\n'
                    f'Sucursal asignada: {sucursal}\n\n'
                    f'Por favor, inicia sesión con estas credenciales en nuestro sistema.\n\n'
                    f'Si tienes alguna pregunta o necesitas ayuda, no dudes en contactar con la administración.\n\n'
                    f'Saludos cordiales,\n'
                    f'Administración - Alquileres María',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                messages.success(request, f'Empleado {nuevo_user.first_name} registrado con éxito.')
                return redirect('usuarios:lista_empleados')

            except Exception as e:
                messages.error(request, f'Error al registrar empleado: {str(e)}')

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
                nuevo_username = form.cleaned_data['email']
                if User.objects.exclude(pk=user.pk).filter(username=nuevo_username).exists():
                    raise Exception("Este username ya está en uso por otro usuario.")
                user.username = nuevo_username
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


#Registro de un cliente como un Empleado


@login_required
@user_passes_test(es_empleado)
def registro_como_empleado(request):
    if request.method == 'POST':
        form = ClientePorEmpleadoForm(request.POST)
        if form.is_valid():
            pswd = get_random_string(length=6)
            email = form.cleaned_data['email']

            user = User.objects.create_user(
                username= email,
                email= email,
                first_name= form.cleaned_data['first_name'],
                last_name= form.cleaned_data['last_name'],
                password= pswd
            )

            # Crear el perfil asociado
            perfil = form.save(commit=False)
            perfil.usuario = user
            perfil.save()

            # Enviar correo con contraseña (opcional)
            send_mail(
                'Tu cuenta en Alquileres María',
                f'Hola {user.first_name}, tu cuenta ha sido registrada con éxito.\nTu contraseña temporal es: {pswd}',
                'no-responder@alquileresmaria.com',
                [user.email],
                fail_silently=True
            )

            messages.success(request, f"Cliente registrado correctamente. Contraseña enviada a {user.email}")
            return redirect('usuarios:registro_como_empleado')
    else:
        form = ClientePorEmpleadoForm()

    return render(request, 'usuarios/registro_como_empleado.html', {
        'form': form
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

                print("Contrasenia nueva: ", nueva_contrasena)

                messages.success(request, 'Se ha enviado una nueva contraseña a tu correo.')
                return redirect('usuarios:login')
            except User.DoesNotExist:
                messages.error(request, 'No se encontró ninguna cuenta con ese correo.',extra_tags='danger')
                return redirect('usuarios:recuperar_contrasena')
    else:
        form = RecuperarContrasenaForm()

    return render(request, 'usuarios/recuperar_contrasena.html', {'form': form})
# Agregar esta nueva vista a tu views.py

@login_required
@user_passes_test(administrador_requerido)
def confirmar_baja_empleado(request):
    """Vista AJAX para confirmar la baja de un empleado con motivo"""
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado_id')
        motivo_baja = request.POST.get('motivo_baja', '').strip()
        
        if not empleado_id:
            return JsonResponse({'success': False, 'error': 'ID de empleado requerido'})
        
        if not motivo_baja:
            return JsonResponse({'success': False, 'error': 'El motivo de la baja es obligatorio'})
        
        try:
            empleado = get_object_or_404(Empleado, id=empleado_id, activo=True)
            
            # Dar de baja al empleado
            empleado.activo = False
            empleado.save()
            
            # Desactivar usuario
            empleado.usuario.is_active = False
            empleado.usuario.save()
            
            # Enviar email al empleado
            try:
                send_mail(
                    'Notificación de Baja - Alquileres María',
                    f'Estimado/a {empleado.usuario.first_name} {empleado.usuario.last_name},\n\n'
                    f'Le informamos que su vinculación laboral con Alquileres María ha finalizado.\n\n'
                    f'Motivo: {motivo_baja}\n\n'
                    f'Agradecemos los servicios prestados y le deseamos éxitos en sus futuros proyectos.\n\n'
                    f'Saludos cordiales,\n'
                    f'Administración - Alquileres María',
                    settings.DEFAULT_FROM_EMAIL,
                    [empleado.usuario.email],
                    fail_silently=False,
                )
            except Exception as e:
                # Si falla el email, registramos el error pero no revertimos la baja
                print(f"Error al enviar email de baja: {str(e)}")
            
            return JsonResponse({
                'success': True, 
                'message': f'Empleado {empleado.usuario.first_name} {empleado.usuario.last_name} dado de baja correctamente.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al dar de baja: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# Modificar la vista lista_empleados existente:
@login_required
@user_passes_test(administrador_requerido)
def lista_empleados(request):
    empleados = Empleado.objects.filter(activo=True)
    return render(request, 'usuarios/lista_empleados.html', {'empleados': empleados})