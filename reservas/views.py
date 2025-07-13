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
from .forms import ReservaForm, CancelarReservaForm, ReservaEmpleadoForm
from vehiculos.models import Vehiculo, Estado, PoliticaReembolso
from reservas.models import Tarjeta
from pagos.models import Pago
from usuarios.models import Empleado
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

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

    monto_pago = request.POST.get('monto_pago', '0')
    try:
        monto_pago = float(monto_pago)
    except ValueError:
        messages.error(request, "El monto total recibido es inválido.")
        return redirect('vehiculos:detalle', vehiculo_id)

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
                        tarjeta = Tarjeta.objects.get(numero=form.cleaned_data['numero_tarjeta']),
                        monto_pago=monto_pago
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
def crear_reserva_Emple(request, vehiculo_id):
    if not hasattr(request.user, 'empleado'):
        return redirect('home')  # Solo empleados acceden

    try:
        estado_disponible = Estado.objects.get(nombre__iexact='disponible')
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, estado=estado_disponible)
    except Estado.DoesNotExist:
        messages.error(request, "Error: No se encontró el estado 'Disponible'.")
        return redirect('vehiculos:lista')

    monto_pago = request.POST.get('monto_pago', '0')
    try:
        monto_pago = float(monto_pago)
    except ValueError:
        messages.error(request, "El monto recibido no es válido.")
        return redirect('vehiculos:detalle', vehiculo_id)

    if request.method == 'POST':
        form = ReservaEmpleadoForm(request.POST, vehiculo=vehiculo, usuario=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    reserva = Reserva(
                        vehiculo=vehiculo,
                        usuario=form.usuario_cliente,
                        fecha_inicio=form.cleaned_data['fecha_inicio'],
                        fecha_fin=form.cleaned_data['fecha_fin'],
                        dni_conductor=form.cleaned_data['dni_conductor'],
                        tarjeta=form.tarjeta_validada,
                        monto_pago=monto_pago
                    )

                    estado_confirmada, _ = EstadoReserva.objects.get_or_create(
                        nombre='Confirmada',
                        defaults={'descripcion': 'Reserva confirmada y activa'}
                    )
                    reserva.estado = estado_confirmada
                    reserva.save()

                    tarjeta = form.tarjeta_validada
                    tarjeta.saldo -= form.total_a_cobrar
                    tarjeta.save()

                    if vehiculo.reservar():
                        messages.success(request, f"Reserva creada exitosamente para {form.usuario_cliente.username}.")
                        return redirect('home')
                    else:
                        reserva.delete()
                        messages.error(request, "No se pudo completar la reserva.")
                        return redirect('home')
            except Exception as e:
                messages.error(request, f"Error al crear la reserva: {str(e)}")
                return redirect('vehiculos:detalle', vehiculo_id)
    else:
        form = ReservaEmpleadoForm(vehiculo=vehiculo, usuario=request.user)

    return render(request, 'reservas/crear_como_Empleado.html', {
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
    model = Reserva
    template_name = 'reservas/reservas_sucursal.html'
    context_object_name = 'reservas'
    paginate_by = 20
    
    def test_func(self):
        try:
            return hasattr(self.request.user, 'empleado') and self.request.user.empleado.activo
        except:
            return False
    
    def get_queryset(self):
        try:
            empleado = self.request.user.empleado
            hoy = date.today()
            
            from django.db.models import Q

            queryset = Reserva.objects.filter(
                vehiculo__sucursal__nombre=empleado.sucursal
            ).filter(
                Q(estado__nombre='Confirmada', fecha_inicio=hoy) |
                Q(estado__nombre='Activa', fecha_fin=hoy)
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
            context['reservas_activas_total'] = reservas_sucursal.filter(estado__nombre='Activa').count()
            context['reservas_confirmadas_total'] = reservas_sucursal.filter(estado__nombre='Confirmada').count()
            
            context['entregas_tardias'] = reservas_sucursal.filter(
                estado__nombre='Confirmada', 
                fecha_inicio__lt=hoy
            )
            
            context['devoluciones_tardias'] = reservas_sucursal.filter(
                estado__nombre='Activa', 
                fecha_fin__lt=hoy
            )
            
            context['total_tardias'] = context['entregas_tardias'].count() + context['devoluciones_tardias'].count()
            
            for devolucion in context['devoluciones_tardias']:
                dias_demora = (hoy - devolucion.fecha_fin).days
                penalizacion = devolucion.vehiculo.precio_por_dia * 2 * dias_demora
                devolucion.dias_demora = dias_demora
                devolucion.penalizacion = penalizacion
                devolucion.total_con_penalizacion = devolucion.calcular_Total() + penalizacion
            
        except Empleado.DoesNotExist:
            context['sucursal_empleado'] = None
            context['fecha_hoy'] = date.today()
            context['total_reservas'] = 0
            context['entregas_hoy'] = 0
            context['devoluciones_hoy'] = 0
            context['total_tardias'] = 0
            context['entregas_tardias'] = []
            context['devoluciones_tardias'] = []
            
        return context

@login_required
def registrar_entrega(request, reserva_id):
    try:
        empleado = request.user.empleado
        if not empleado.activo:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('reservas:reservas_sucursal')
    except Empleado.DoesNotExist:
        messages.error(request, "Solo los empleados pueden registrar entregas.")
        return redirect('home')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if reserva.vehiculo.sucursal.nombre != empleado.sucursal:
        messages.error(request, "Esta reserva no pertenece a su sucursal.")
        return redirect('reservas:reservas_sucursal')
    
    if reserva.estado.nombre != 'Confirmada':
        messages.error(request, f"No se puede entregar. La reserva está en estado: {reserva.estado.nombre}")
        return redirect('reservas:reservas_sucursal')
    
    if request.method == 'POST':
        incluir_seguro = request.POST.get('incluir_seguro') == 'on'
        incluir_conductor = request.POST.get('incluir_conductor') == 'on'
        dni_conductor_adicional = request.POST.get('dni_conductor_adicional', '').strip()
        
        try:
            if incluir_conductor:
                if not dni_conductor_adicional:
                    messages.error(request, 'Debe proporcionar el DNI del conductor adicional')
                    return redirect('reservas:registrar_entrega', reserva_id)
                
                reservas_conflicto = Reserva.objects.filter(
                    dni_conductor=dni_conductor_adicional,
                    estado__nombre__in=['Confirmada', 'Activa'],
                    fecha_inicio__lte=reserva.fecha_fin,
                    fecha_fin__gte=reserva.fecha_inicio
                ).exclude(id=reserva.id)
                
                if reservas_conflicto.exists():
                    reserva_conflicto = reservas_conflicto.first()
                    messages.error(request, f'El DNI {dni_conductor_adicional} ya tiene una reserva {reserva_conflicto.estado.nombre.lower()} del {reserva_conflicto.fecha_inicio.strftime("%d/%m/%Y")} al {reserva_conflicto.fecha_fin.strftime("%d/%m/%Y")}. No se pueden tener dos vehículos alquilados simultáneamente.')
                    return redirect('reservas:registrar_entrega', reserva_id)
            
            total_original = reserva.calcular_Total()
            costo_adicional = 0
            
            if incluir_seguro:
                costo_adicional += total_original * Decimal('0.20')

            if incluir_conductor:
                costo_adicional += total_original * Decimal('0.15')
            
            # Validar saldo sin mostrarlo al usuario
            if costo_adicional > 0 and reserva.tarjeta.saldo < costo_adicional:
                messages.error(request, f'Saldo insuficiente en la tarjeta para procesar los servicios adicionales solicitados (${costo_adicional:.2f}). Por favor, contacte al cliente para actualizar el método de pago.')
                return redirect('reservas:registrar_entrega', reserva_id)
            
            with transaction.atomic():
                try:
                    estado_activa = EstadoReserva.objects.get(nombre='Activa')
                except EstadoReserva.DoesNotExist:
                    messages.error(request, 'Error: No se encontró el estado "Activa" en el sistema.')
                    return redirect('reservas:registrar_entrega', reserva_id)
                
                if costo_adicional > 0:
                    reserva.tarjeta.saldo -= costo_adicional
                    reserva.tarjeta.save()
                
                Reserva.objects.filter(id=reserva.id).update(estado=estado_activa)
                reserva.refresh_from_db()
                
                hoy = date.today()
                es_tardia = reserva.fecha_inicio < hoy
                
                mensaje_base = f"✅ Entrega registrada exitosamente. Vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} entregado a {reserva.usuario.first_name} {reserva.usuario.last_name}."
                
                detalles_adicionales = []
                if incluir_seguro:
                    detalles_adicionales.append(f"Seguro completo: ${total_original * Decimal('0.20'):.2f}")
                if incluir_conductor:
                    detalles_adicionales.append(f"Conductor adicional: ${total_original * Decimal('0.15'):.2f}")
                
                if detalles_adicionales:
                    mensaje_base += f" 💳 Servicios adicionales cobrados: {', '.join(detalles_adicionales)}. Total adicional: ${costo_adicional:.2f}"
                
                if es_tardia:
                    dias_retraso = (hoy - reserva.fecha_inicio).days
                    mensaje_base += f" ⚠️ Entrega tardía con {dias_retraso} día(s) de retraso."
                
                messages.success(request, mensaje_base)
                return redirect('reservas:reservas_sucursal')
                
        except Exception as e:
            messages.error(request, f'Error al procesar la entrega: {str(e)}')
            return redirect('reservas:registrar_entrega', reserva_id)
    
    hoy = date.today()
    es_tardia = reserva.fecha_inicio < hoy
    
    total_original = reserva.calcular_Total()
    costo_seguro = total_original * Decimal('0.20')
    costo_conductor = total_original * Decimal('0.15')
    
    context = {
        'reserva': reserva,
        'empleado': empleado,
        'es_tardia': es_tardia,
        'total_original': total_original,
        'costo_seguro': costo_seguro,
        'costo_conductor': costo_conductor,
    }
    
    if es_tardia:
        dias_retraso = (hoy - reserva.fecha_inicio).days
        context['dias_retraso'] = dias_retraso
    
    return render(request, 'reservas/entrega_vehiculo.html', context)

@login_required
def registrar_devolucion_simple(request, reserva_id):
    try:
        empleado = request.user.empleado
        if not empleado.activo:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('reservas:reservas_sucursal')
    except Empleado.DoesNotExist:
        messages.error(request, "Solo los empleados pueden registrar devoluciones.")
        return redirect('home')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if not _validar_devolucion_basica(reserva, empleado, request):
        return redirect('reservas:reservas_sucursal')
    
    hoy = date.today()
    es_tardia = reserva.fecha_fin < hoy
    
    try:
        with transaction.atomic():
            estado_completada = EstadoReserva.objects.get(nombre='Completada')
            
            Reserva.objects.filter(id=reserva.id).update(estado=estado_completada)
            reserva.refresh_from_db()
            
            if es_tardia:
                dias_demora = (hoy - reserva.fecha_fin).days
                penalizacion = reserva.vehiculo.precio_por_dia * 2 * dias_demora
                
                if reserva.tarjeta.saldo >= penalizacion:
                    reserva.tarjeta.saldo -= penalizacion
                    reserva.tarjeta.save()
                    
                    messages.success(
                        request, 
                        f"Devolución TARDÍA registrada exitosamente. Vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} devuelto con {dias_demora} día(s) de retraso. Penalización cobrada: ${penalizacion:.2f}"
                    )
                else:
                    messages.warning(
                        request, 
                        f"Devolución TARDÍA registrada pero saldo insuficiente para penalización. Retraso: {dias_demora} día(s). Penalización pendiente: ${penalizacion:.2f}"
                    )
            else:
                messages.success(
                    request, 
                    f"Devolución registrada exitosamente. Vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo} devuelto y disponible para nuevas reservas."
                )
            
            try:
                estado_disponible = Estado.objects.get(nombre='Disponible')
                Vehiculo.objects.filter(id=reserva.vehiculo.id).update(estado=estado_disponible)
            except Estado.DoesNotExist:
                pass
        
    except EstadoReserva.DoesNotExist:
        messages.error(request, "Error: No se encontró el estado 'Completada' en el sistema.")
    except Exception as e:
        messages.error(request, f"Error al registrar la devolución: {str(e)}")
    
    return redirect('reservas:reservas_sucursal')

@login_required
def registrar_devolucion_mantenimiento(request, reserva_id):
    try:
        empleado = request.user.empleado
        if not empleado.activo:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('reservas:reservas_sucursal')
    except Empleado.DoesNotExist:
        messages.error(request, "Solo los empleados pueden registrar devoluciones.")
        return redirect('home')
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if not _validar_devolucion_basica(reserva, empleado, request):
        return redirect('reservas:reservas_sucursal')
    
    hoy = date.today()
    es_tardia = reserva.fecha_fin < hoy
    
    try:
        with transaction.atomic():
            estado_completada = EstadoReserva.objects.get(nombre='Completada')
            
            Reserva.objects.filter(id=reserva.id).update(estado=estado_completada)
            reserva.refresh_from_db()
            
            if es_tardia:
                dias_demora = (hoy - reserva.fecha_fin).days
                penalizacion = reserva.vehiculo.precio_por_dia * 2 * dias_demora
                
                if reserva.tarjeta.saldo >= penalizacion:
                    reserva.tarjeta.saldo -= penalizacion
                    reserva.tarjeta.save()
                    
                    messages.info(
                        request, 
                        f"Penalización por retraso cobrada: ${penalizacion:.2f} ({dias_demora} día(s) × ${reserva.vehiculo.precio_por_dia * 2:.2f})"
                    )
                else:
                    messages.warning(
                        request, 
                        f"Saldo insuficiente para penalización. Penalización pendiente: ${penalizacion:.2f}"
                    )
            
            resultado_mantenimiento = _procesar_mantenimiento_vehiculo(reserva.vehiculo, empleado)
            
            if resultado_mantenimiento['success']:
                if es_tardia:
                    messages.success(
                        request, 
                        f"Devolución TARDÍA con mantenimiento registrada. {resultado_mantenimiento['message']}"
                    )
                else:
                    messages.success(
                        request, 
                        f"Devolución con mantenimiento registrada. {resultado_mantenimiento['message']}"
                    )
                    
                if resultado_mantenimiento.get('reservas_reasignadas', 0) > 0:
                    messages.info(
                        request, 
                        f"Se reasignaron {resultado_mantenimiento['reservas_reasignadas']} reservas a vehículos alternativos. Los clientes han sido notificados por email."
                    )
                
                if resultado_mantenimiento.get('reservas_canceladas', 0) > 0:
                    messages.warning(
                        request, 
                        f"Se cancelaron {resultado_mantenimiento['reservas_canceladas']} reservas por falta de vehículos alternativos. Los clientes han sido notificados y reembolsados."
                    )
            else:
                messages.warning(request, f"Devolución completada pero: {resultado_mantenimiento['message']}")
        
    except EstadoReserva.DoesNotExist:
        messages.error(request, "Error: No se encontró el estado 'Completada' en el sistema.")
    except Exception as e:
        messages.error(request, f"Error al registrar la devolución: {str(e)}")
    
    return redirect('reservas:reservas_sucursal')

def _validar_devolucion_basica(reserva, empleado, request):
    if reserva.vehiculo.sucursal.nombre != empleado.sucursal:
        messages.error(request, "Esta reserva no pertenece a su sucursal.")
        return False
    
    if reserva.estado.nombre != 'Activa':
        messages.error(request, f"No se puede devolver. La reserva está en estado: {reserva.estado.nombre}")
        return False
    
    return True

def _procesar_mantenimiento_vehiculo(vehiculo, empleado):
    try:
        estado_mantenimiento, created = Estado.objects.get_or_create(
            nombre='Mantenimiento',
            defaults={'descripcion': 'Vehículo en mantenimiento'}
        )
        
        Vehiculo.objects.filter(id=vehiculo.id).update(estado=estado_mantenimiento)
        
        fecha_inicio_mantenimiento = date.today() + timedelta(days=1)
        fecha_fin_mantenimiento = fecha_inicio_mantenimiento + timedelta(days=2)
        
        reservas_afectadas = Reserva.objects.filter(
            vehiculo=vehiculo,
            estado__nombre='Confirmada',
            fecha_inicio__lte=fecha_fin_mantenimiento,
            fecha_fin__gte=fecha_inicio_mantenimiento
        )
        
        reservas_reasignadas = 0
        reservas_canceladas = 0
        
        for reserva_afectada in reservas_afectadas:
            vehiculo_alternativo = _buscar_vehiculo_alternativo(vehiculo, reserva_afectada, empleado)
            
            if vehiculo_alternativo:
                vehiculo_original = reserva_afectada.vehiculo
                Reserva.objects.filter(id=reserva_afectada.id).update(vehiculo=vehiculo_alternativo)
                reserva_afectada.refresh_from_db()
                
                _enviar_notificacion_cambio_vehiculo(reserva_afectada, vehiculo_original, vehiculo_alternativo)
                
                reservas_reasignadas += 1
            else:
                vehiculo_original = reserva_afectada.vehiculo
                
                estado_cancelada, created = EstadoReserva.objects.get_or_create(
                    nombre='Cancelada por Admin',
                    defaults={'descripcion': 'Reserva cancelada por administrador'}
                )
                
                Reserva.objects.filter(id=reserva_afectada.id).update(
                    estado=estado_cancelada,
                    motivo_cancelacion=f'Cancelada por mantenimiento del vehículo {vehiculo_original.marca} {vehiculo_original.modelo} - No hay vehículos alternativos disponibles'
                )
                reserva_afectada.refresh_from_db()
                
                _realizar_reembolso_completo(reserva_afectada)
                
                _enviar_notificacion_cancelacion_mantenimiento(reserva_afectada, vehiculo_original, fecha_inicio_mantenimiento, fecha_fin_mantenimiento)
                
                reservas_canceladas += 1
        
        return {
            'success': True,
            'message': f"Vehículo {vehiculo.marca} {vehiculo.modelo} programado para mantenimiento del {fecha_inicio_mantenimiento.strftime('%d/%m/%Y')} al {fecha_fin_mantenimiento.strftime('%d/%m/%Y')}.",
            'reservas_reasignadas': reservas_reasignadas,
            'reservas_canceladas': reservas_canceladas
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error al procesar mantenimiento: {str(e)}"
        }

def _buscar_vehiculo_alternativo(vehiculo_original, reserva, empleado):
    try:
        estado_disponible = Estado.objects.get(nombre='Disponible')
        
        vehiculos_alternativos = Vehiculo.objects.filter(
            sucursal__nombre=empleado.sucursal,
            estado=estado_disponible,
            precio_por_dia__gt=vehiculo_original.precio_por_dia
        ).exclude(
            id=vehiculo_original.id
        ).order_by('precio_por_dia')
        
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

def _realizar_reembolso_completo(reserva):
    try:
        monto_reembolso = reserva.calcular_Total()
        
        tarjeta = reserva.tarjeta
        tarjeta.saldo += monto_reembolso
        tarjeta.save()
        
        return monto_reembolso
        
    except Exception as e:
        print(f"Error realizando reembolso: {str(e)}")
        return 0

def _enviar_notificacion_cambio_vehiculo(reserva, vehiculo_original, vehiculo_nuevo):
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
        print(f"Error enviando email de cambio: {str(e)}")

def _enviar_notificacion_cancelacion_mantenimiento(reserva, vehiculo_original, fecha_inicio_mantenimiento, fecha_fin_mantenimiento):
    try:
        monto_reembolso = reserva.calcular_Total()
        
        subject = f'Cancelación de reserva por mantenimiento - Alquileres María'
        
        context = {
            'reserva': reserva,
            'vehiculo_original': vehiculo_original,
            'cliente_nombre': f"{reserva.usuario.first_name} {reserva.usuario.last_name}",
            'fecha_inicio_mantenimiento': fecha_inicio_mantenimiento,
            'fecha_fin_mantenimiento': fecha_fin_mantenimiento,
            'monto_reembolso': monto_reembolso,
        }
        
        message = render_to_string('reservas/emails/cancelacion_mantenimiento.html', context)
        
        send_mail(
            subject=subject,
            message='',
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reserva.usuario.email],
            fail_silently=False,
        )
        
    except Exception as e:
        print(f"Error enviando email de cancelación: {str(e)}")