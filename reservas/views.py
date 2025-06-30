#reservas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Reserva, EstadoReserva
from .forms import ReservaForm, CancelarReservaForm
from vehiculos.models import Vehiculo, Estado, PoliticaReembolso
from reservas.models import Tarjeta
from pagos.models import Pago
from usuarios.models import Empleado
from django.utils import timezone
from datetime import date, timedelta

class ReservaListView(LoginRequiredMixin, ListView):
    model = Reserva
    template_name = 'reservas/reserva_list.html'
    context_object_name = 'reservas'
    paginate_by = 10
    
    def get_queryset(self):
        # Mostrar solo las reservas del usuario actual
        return Reserva.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')

class ReservaDetailView(LoginRequiredMixin, DetailView):
    model = Reserva
    template_name = 'reservas/reserva_detail.html'
    context_object_name = 'reserva'
    
    def get_queryset(self):
        # Asegurar que el usuario solo pueda ver sus propias reservas
        return Reserva.objects.filter(usuario=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reserva = self.get_object()
        context['puede_cancelar'] = reserva.puede_cancelar_usuario()
        context['form_cancelar'] = CancelarReservaForm()
        context['total_a_pagar'] = reserva.calcular_Total()
        return context
    

@login_required
def crear_reserva(request, vehiculo_id):
    # Buscar el estado "Disponible" y el vehículo con ese estado
    try:
        estado_disponible = Estado.objects.get(nombre__iexact='disponible')
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, estado=estado_disponible)
    except Estado.DoesNotExist:
        messages.error(request, "Error: No se encontró el estado 'Disponible' en el sistema.")
        return redirect('vehiculos:lista')
    
    if request.method == 'POST':
        form = ReservaForm(request.POST, vehiculo=vehiculo, usuario=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear la reserva
                    reserva = Reserva(
                        vehiculo=vehiculo,
                        usuario=request.user,
                        fecha_inicio=form.cleaned_data['fecha_inicio'],
                        fecha_fin=form.cleaned_data['fecha_fin'],
                        dni_conductor=form.cleaned_data['dni_conductor'],
                        tarjeta = Tarjeta.objects.get(numero=form.cleaned_data['numero_tarjeta'])
                    )
                    
                    # Obtener el estado "Confirmada" para la reserva
                    try:
                        estado_confirmada = EstadoReserva.objects.get(nombre__iexact='confirmada')
                        reserva.estado = estado_confirmada
                    except EstadoReserva.DoesNotExist:
                        # Si no existe, crear el estado o usar el primero disponible
                        estado_confirmada, created = EstadoReserva.objects.get_or_create(
                            nombre='Confirmada',
                            defaults={'descripcion': 'Reserva confirmada y activa'}
                        )
                        reserva.estado = estado_confirmada
                    

                    reserva.save()
                    # Descontar saldo de la tarjeta validada solo si la reserva se creó exitosamente
                    tarjeta = form.tarjeta_validada
                    tarjeta.saldo -= form.total_a_cobrar
                    tarjeta.save()
                    # Cambiar el estado del vehículo a reservado
                    if vehiculo.reservar():
                        messages.success(request, f"Reserva creada exitosamente. Vehículo {vehiculo.marca} {vehiculo.modelo} reservado.")
                        return redirect('reservas:lista')
                    else:
                        # Si no se pudo reservar el vehículo, eliminar la reserva
                        reserva.delete()
                        messages.error(request, "No se pudo completar la reserva. El vehículo no está disponible.")
                        return redirect('reservas:lista')
                        
            except Exception as e:
                messages.error(request, f"Error al crear la reserva: {str(e)}")
                return redirect('vehiculos:detalle', vehiculo_id)
    else:
        form = ReservaForm(vehiculo=vehiculo, usuario=request.user)
    
    return render(request, 'reservas/crear_reserva.html', {
        'form': form,
        'vehiculo': vehiculo
    })

@login_required
def cancelar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, id=pk, usuario=request.user)
    
    try:
        with transaction.atomic():
            # Obtener el estado "Cancelada" para la reserva
            try:
                estado_cancelada = EstadoReserva.objects.get(nombre__iexact='cancelada')
            except EstadoReserva.DoesNotExist:
                # Si no existe, crearlo
                estado_cancelada, created = EstadoReserva.objects.get_or_create(
                    nombre='Cancelada',
                    defaults={'descripcion': 'Reserva cancelada por el usuario'}
                )
                    
            reserva.estado = estado_cancelada
            reserva.motivo_cancelacion = 'Cancelada desde Lista'
            reserva.save()

            vehiculo = reserva.vehiculo
            _Realizar_Reembolso(reserva, request)

            # Liberar el vehículo usando el nuevo método
            if vehiculo.liberar():
                messages.success(request, f"Reserva cancelada exitosamente. Vehículo {vehiculo.marca} {vehiculo.modelo} liberado.")
            else:
                messages.warning(request, f"Reserva cancelada exitosamente.")
                    
            return redirect('reservas:lista')
                    
    except Exception as e:
        messages.error(request, f"Error al cancelar la reserva: {str(e)}")
        return redirect('reservas:lista')
    return redirect('reservas:lista')

def _Realizar_Reembolso(reserva, request):
 
    monto_reembolso = reserva.calcular_Reembolso()

    # Obtener pago y tarjeta
    tarjeta = reserva.tarjeta
    tarjeta.saldo += monto_reembolso
    tarjeta.save()   
    messages.success(request, f"Se ha reembolsado ${monto_reembolso:.2f} a la tarjeta terminada en {tarjeta.numero[-4:]}")



@login_required
def admin_cancelar_reserva(request, pk):
    # Solo para administradores
    if not request.user.is_staff:
        messages.error(request, "No tiene permisos para realizar esta acción.")
        return redirect('home')
    
    reserva = get_object_or_404(Reserva, id=pk)
    
    if request.method == 'POST':
        form = CancelarReservaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Obtener el estado "Cancelada por Admin" para la reserva
                    try:
                        estado_cancelada = EstadoReserva.objects.get(nombre__iexact='cancelada por admin')
                    except EstadoReserva.DoesNotExist:
                        # Si no existe, crearlo
                        estado_cancelada, created = EstadoReserva.objects.get_or_create(
                            nombre='Cancelada por Admin',
                            defaults={'descripcion': 'Reserva cancelada por un administrador'}
                        )
                    
                    reserva.estado = estado_cancelada
                    reserva.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
                    reserva.save()
                    
                    # Liberar el vehículo usando el nuevo método
                    vehiculo = reserva.vehiculo
                    if vehiculo.liberar():
                        messages.success(request, f"Reserva cancelada exitosamente por administrador. Vehículo {vehiculo.marca} {vehiculo.modelo} liberado.")
                    else:
                        messages.warning(request, f"Reserva cancelada, pero no se pudo liberar automáticamente el vehículo {vehiculo.marca} {vehiculo.modelo}.")
                    
                    return redirect('admin:reservas_reserva_changelist')
                    
            except Exception as e:
                messages.error(request, f"Error al cancelar la reserva: {str(e)}")
                return redirect('admin:reservas_reserva_changelist')
    else:
        form = CancelarReservaForm()
    
    return render(request, 'reservas/admin_cancelar_reserva.html', {
        'form': form,
        'reserva': reserva
    })

class ReservaSucursalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista para que los empleados vean las reservas de su sucursal que requieren acción hoy"""
    model = Reserva
    template_name = 'reservas/reservas_sucursal.html'
    context_object_name = 'reservas'
    paginate_by = 20
    
    def test_func(self):
        """Verificar que el usuario sea empleado"""
        try:
            return hasattr(self.request.user, 'empleado') and self.request.user.empleado.activo
        except:
            return False
    
    def get_queryset(self):
        """Obtener reservas de la sucursal del empleado que requieren acción hoy"""
        try:
            empleado = self.request.user.empleado
            hoy = date.today()
            
            # Obtener reservas que requieren acción hoy:
            # 1. Reservas CONFIRMADAS con fecha de inicio = hoy (para entrega)
            # 2. Reservas ACTIVAS con fecha de fin = hoy (para devolución)
            from django.db.models import Q

            queryset = Reserva.objects.filter(
                vehiculo__sucursal__nombre=empleado.sucursal  # Vehículos de la sucursal del empleado
            ).filter(
                Q(estado__nombre='Confirmada', fecha_inicio=hoy) |  # Entregas de hoy
                Q(estado__nombre='Activa', fecha_fin=hoy)           # Devoluciones de hoy
            ).select_related(
                'vehiculo', 'usuario', 'estado', 'vehiculo__sucursal'
            ).order_by('estado__nombre', 'fecha_inicio', 'vehiculo__marca', 'vehiculo__modelo')
            
            return queryset
            
        except Empleado.DoesNotExist:
            return Reserva.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            empleado = self.request.user.empleado
            hoy = date.today()
            
            context['sucursal_empleado'] = empleado.sucursal
            context['fecha_hoy'] = hoy
            
            # Estadísticas específicas para hoy
            reservas_sucursal = Reserva.objects.filter(vehiculo__sucursal__nombre=empleado.sucursal)
            
            context['entregas_hoy'] = reservas_sucursal.filter(
                estado__nombre='Confirmada', 
                fecha_inicio=hoy
            ).count()
            
            context['devoluciones_hoy'] = reservas_sucursal.filter(
                estado__nombre='Activa', 
                fecha_fin=hoy
            ).count()
            
            context['total_reservas'] = context['entregas_hoy'] + context['devoluciones_hoy']
            
            # Estadísticas adicionales
            context['reservas_activas_total'] = reservas_sucursal.filter(estado__nombre='Activa').count()
            context['reservas_confirmadas_total'] = reservas_sucursal.filter(estado__nombre='Confirmada').count()
            
        except Empleado.DoesNotExist:
            context['sucursal_empleado'] = None
            context['fecha_hoy'] = date.today()
            context['total_reservas'] = 0
            context['entregas_hoy'] = 0
            context['devoluciones_hoy'] = 0
            
        return context

@login_required
def registrar_entrega(request, reserva_id):
    """Vista para registrar la entrega de un vehículo (cambiar estado de Confirmada a Activa)"""
    
    # Verificar que el usuario sea empleado
    try:
        empleado = request.user.empleado
        if not empleado.activo:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('reservas:reservas_sucursal')
    except Empleado.DoesNotExist:
        messages.error(request, "Solo los empleados pueden registrar entregas.")
        return redirect('home')
    
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificar que la reserva pertenezca a la sucursal del empleado
    if reserva.vehiculo.sucursal.nombre != empleado.sucursal:
        messages.error(request, "Esta reserva no pertenece a su sucursal.")
        return redirect('reservas:reservas_sucursal')
    
    # Verificar que la reserva esté en estado "Confirmada"
    if reserva.estado.nombre != 'Confirmada':
        messages.error(request, f"No se puede entregar. La reserva está en estado: {reserva.estado.nombre}")
        return redirect('reservas:reservas_sucursal')
    
    # Verificar que sea el día de entrega
    if reserva.fecha_inicio != date.today():
        messages.error(request, "Solo se pueden registrar entregas en la fecha de inicio de la reserva.")
        return redirect('reservas:reservas_sucursal')
    
    try:
        with transaction.atomic():
            # Obtener el estado "Activa"
            try:
                estado_activa = EstadoReserva.objects.get(nombre='Activa')
            except EstadoReserva.DoesNotExist:
                messages.error(request, "Error: No se encontró el estado 'Activa' en el sistema.")
                return redirect('reservas:reservas_sucursal')
        
            # Cambiar el estado de la reserva usando update() para evitar validaciones del modelo
            Reserva.objects.filter(id=reserva.id).update(estado=estado_activa)
        
            # Refrescar el objeto desde la base de datos
            reserva.refresh_from_db()
        
            messages.success(
                request, 
                f"✅ Entrega registrada exitosamente. Reserva de {reserva.vehiculo.marca} {reserva.vehiculo.modelo} "
                f"(Patente: {reserva.vehiculo.patente}) para {reserva.usuario.first_name} {reserva.usuario.last_name}."
            )
        
    except Exception as e:
        messages.error(request, f"Error al registrar la entrega: {str(e)}")
    
    return redirect('reservas:reservas_sucursal')

@login_required
def registrar_devolucion_simple(request, reserva_id):
    """Vista para registrar devolución SIN mantenimiento"""
    
    # Verificar que el usuario sea empleado
    try:
        empleado = request.user.empleado
        if not empleado.activo:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('reservas:reservas_sucursal')
    except Empleado.DoesNotExist:
        messages.error(request, "Solo los empleados pueden registrar devoluciones.")
        return redirect('home')
    
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificaciones básicas
    if not _validar_devolucion(reserva, empleado, request):
        return redirect('reservas:reservas_sucursal')
    
    try:
        with transaction.atomic():
            # Obtener el estado "Completada"
            estado_completada = EstadoReserva.objects.get(nombre='Completada')
            
            # Cambiar el estado de la reserva
            Reserva.objects.filter(id=reserva.id).update(estado=estado_completada)
            reserva.refresh_from_db()
            
            # Liberar el vehículo (cambiar a disponible)
            try:
                estado_disponible = Estado.objects.get(nombre='Disponible')
                Vehiculo.objects.filter(id=reserva.vehiculo.id).update(estado=estado_disponible)
            except Estado.DoesNotExist:
                pass
        
            messages.success(
                request, 
                f"✅ Devolución registrada exitosamente. Vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} "
                f"(Patente: {reserva.vehiculo.patente}) devuelto y disponible para nuevas reservas."
            )
        
    except EstadoReserva.DoesNotExist:
        messages.error(request, "Error: No se encontró el estado 'Completada' en el sistema.")
    except Exception as e:
        messages.error(request, f"Error al registrar la devolución: {str(e)}")
    
    return redirect('reservas:reservas_sucursal')

@login_required
def registrar_devolucion_mantenimiento(request, reserva_id):
    """Vista para registrar devolución CON mantenimiento"""
    
    # Verificar que el usuario sea empleado
    try:
        empleado = request.user.empleado
        if not empleado.activo:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('reservas:reservas_sucursal')
    except Empleado.DoesNotExist:
        messages.error(request, "Solo los empleados pueden registrar devoluciones.")
        return redirect('home')
    
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Verificaciones básicas
    if not _validar_devolucion(reserva, empleado, request):
        return redirect('reservas:reservas_sucursal')
    
    try:
        with transaction.atomic():
            # Obtener el estado "Completada"
            estado_completada = EstadoReserva.objects.get(nombre='Completada')
            
            # Cambiar el estado de la reserva
            Reserva.objects.filter(id=reserva.id).update(estado=estado_completada)
            reserva.refresh_from_db()
            
            # Procesar mantenimiento del vehículo
            resultado_mantenimiento = _procesar_mantenimiento_vehiculo(reserva.vehiculo, empleado)
            
            if resultado_mantenimiento['success']:
                messages.success(
                    request, 
                    f"✅ Devolución registrada exitosamente. {resultado_mantenimiento['message']}"
                )
                if resultado_mantenimiento.get('reservas_reasignadas', 0) > 0:
                    messages.info(
                        request, 
                        f"📧 Se reasignaron {resultado_mantenimiento['reservas_reasignadas']} reservas a vehículos alternativos. "
                        f"Los clientes han sido notificados por email."
                    )
            else:
                messages.warning(request, f"⚠️ Devolución completada pero: {resultado_mantenimiento['message']}")
        
    except EstadoReserva.DoesNotExist:
        messages.error(request, "Error: No se encontró el estado 'Completada' en el sistema.")
    except Exception as e:
        messages.error(request, f"Error al registrar la devolución: {str(e)}")
    
    return redirect('reservas:reservas_sucursal')

def _validar_devolucion(reserva, empleado, request):
    """Función auxiliar para validar una devolución"""
    
    # Verificar que la reserva pertenezca a la sucursal del empleado
    if reserva.vehiculo.sucursal.nombre != empleado.sucursal:
        messages.error(request, "Esta reserva no pertenece a su sucursal.")
        return False
    
    # Verificar que la reserva esté en estado "Activa"
    if reserva.estado.nombre != 'Activa':
        messages.error(request, f"No se puede devolver. La reserva está en estado: {reserva.estado.nombre}")
        return False
    
    # Verificar que sea el día de devolución
    if reserva.fecha_fin != date.today():
        messages.error(request, "Solo se pueden registrar devoluciones en la fecha de fin de la reserva.")
        return False
    
    return True

def _procesar_mantenimiento_vehiculo(vehiculo, empleado):
    """Procesa el mantenimiento de un vehículo y reasigna reservas si es necesario"""
    try:
        # Cambiar estado del vehículo a mantenimiento
        estado_mantenimiento, created = Estado.objects.get_or_create(
            nombre='Mantenimiento',
            defaults={'descripcion': 'Vehículo en mantenimiento'}
        )
        
        Vehiculo.objects.filter(id=vehiculo.id).update(estado=estado_mantenimiento)
        
        # Calcular fechas de mantenimiento (3 días)
        fecha_inicio_mantenimiento = date.today() + timedelta(days=1)  # Mañana
        fecha_fin_mantenimiento = fecha_inicio_mantenimiento + timedelta(days=2)  # 3 días total
        
        # Buscar reservas confirmadas afectadas
        reservas_afectadas = Reserva.objects.filter(
            vehiculo=vehiculo,
            estado__nombre='Confirmada',
            fecha_inicio__lte=fecha_fin_mantenimiento,
            fecha_fin__gte=fecha_inicio_mantenimiento
        )
        
        reservas_reasignadas = 0
        
        for reserva_afectada in reservas_afectadas:
            # Buscar vehículo alternativo
            vehiculo_alternativo = _buscar_vehiculo_alternativo(vehiculo, reserva_afectada, empleado)
            
            if vehiculo_alternativo:
                # Reasignar reserva
                vehiculo_original = reserva_afectada.vehiculo
                Reserva.objects.filter(id=reserva_afectada.id).update(vehiculo=vehiculo_alternativo)
                reserva_afectada.refresh_from_db()
                
                # Enviar notificación por email
                _enviar_notificacion_cambio_vehiculo(reserva_afectada, vehiculo_original, vehiculo_alternativo)
                
                reservas_reasignadas += 1
        
        return {
            'success': True,
            'message': f"Vehículo {vehiculo.marca} {vehiculo.modelo} programado para mantenimiento del {fecha_inicio_mantenimiento.strftime('%d/%m/%Y')} al {fecha_fin_mantenimiento.strftime('%d/%m/%Y')}.",
            'reservas_reasignadas': reservas_reasignadas
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error al procesar mantenimiento: {str(e)}"
        }

def _buscar_vehiculo_alternativo(vehiculo_original, reserva, empleado):
    """Busca un vehículo alternativo disponible con precio mayor"""
    try:
        estado_disponible = Estado.objects.get(nombre='Disponible')
        
        # Buscar vehículos disponibles en la misma sucursal con precio mayor
        vehiculos_alternativos = Vehiculo.objects.filter(
            sucursal__nombre=empleado.sucursal,
            estado=estado_disponible,
            precio_por_dia__gt=vehiculo_original.precio_por_dia
        ).exclude(
            id=vehiculo_original.id
        ).order_by('precio_por_dia')  # Ordenar por precio para tomar el más barato de los más caros
        
        # Verificar disponibilidad en las fechas de la reserva
        for vehiculo_candidato in vehiculos_alternativos:
            reservas_conflicto = Reserva.objects.filter(
                vehiculo=vehiculo_candidato,
                estado__nombre__in=['Confirmada', 'Activa'],
                fecha_inicio__lte=reserva.fecha_fin,
                fecha_fin__gte=reserva.fecha_inicio
            ).exclude(id=reserva.id)
            
            if not reservas_conflicto.exists():
                return vehiculo_candidato
        
        return None
        
    except Estado.DoesNotExist:
        return None

def _enviar_notificacion_cambio_vehiculo(reserva, vehiculo_original, vehiculo_nuevo):
    """Envía notificación por email sobre el cambio de vehículo"""
    try:
        diferencia_precio = (vehiculo_nuevo.precio_por_dia - vehiculo_original.precio_por_dia) * (reserva.fecha_fin - reserva.fecha_inicio).days
        
        subject = f'Cambio de vehículo en su reserva - Alquileres María'
        
        context = {
            'reserva': reserva,
            'vehiculo_original': vehiculo_original,
            'vehiculo_nuevo': vehiculo_nuevo,
            'diferencia_precio': diferencia_precio,
            'cliente_nombre': f"{reserva.usuario.first_name} {reserva.usuario.last_name}",
        }
        
        message = render_to_string('reservas/emails/cambio_vehiculo.html', context)
        
        send_mail(
            subject=subject,
            message='',
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reserva.usuario.email],
            fail_silently=False,
        )
        
    except Exception as e:
        print(f"Error enviando email: {str(e)}")