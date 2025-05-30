#reservas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from .models import Reserva, EstadoReserva
from .forms import ReservaForm, CancelarReservaForm
from vehiculos.models import Vehiculo, Estado, PoliticaReembolso
from reservas.models import Tarjeta
from pagos.models import Pago
from django.utils import timezone

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
    
    # Verificar si la reserva puede ser cancelada por el usuario
    if not reserva.puede_cancelar_usuario():
        messages.error(request, "No es posible cancelar la reserva con menos de 24 horas de anticipación.")
        return redirect('reservas:lista')
    
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