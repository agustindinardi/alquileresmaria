from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.urls import reverse
from .models import Reserva, EstadoReserva
from .forms import ReservaForm, CancelarReservaForm
from vehiculos.models import Vehiculo
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
        return context

@login_required
def crear_reserva(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, disponible=True)
    
    if request.method == 'POST':
        form = ReservaForm(request.POST, vehiculo=vehiculo, usuario=request.user)
        if form.is_valid():
            # Crear la reserva
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.vehiculo = vehiculo
            
            # Obtener el estado "Pendiente"
            estado_pendiente = EstadoReserva.objects.get(nombre='Pendiente')
            reserva.estado = estado_pendiente
            
            reserva.save()
            messages.success(request, "Reserva creada exitosamente. Proceda a realizar el pago.")
            return redirect('pagos:procesar_pago', reserva_id=reserva.id)
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
        messages.error(request, "No es posible cancelar la reserva con menos de 24 horas de anticipacion.")
        return redirect('reservas:detalle', pk=reserva.id)
    
    if request.method == 'POST':
        form = CancelarReservaForm(request.POST)
        if form.is_valid():
            # Obtener el estado "Cancelada"
            estado_cancelada = EstadoReserva.objects.get(nombre='Cancelada')
            reserva.estado = estado_cancelada
            reserva.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
            reserva.save()
            
            messages.success(request, "Reserva cancelada exitosamente.")
            return redirect('reservas:lista')
    else:
        form = CancelarReservaForm()
    
    return render(request, 'reservas/cancelar_reserva.html', {
        'form': form,
        'reserva': reserva
    })

@login_required
def admin_cancelar_reserva(request, pk):
    # Solo para administradores
    if not request.user.is_staff:
        messages.error(request, "No tiene permisos para realizar esta accion.")
        return redirect('home')
    
    reserva = get_object_or_404(Reserva, id=pk)
    
    if request.method == 'POST':
        form = CancelarReservaForm(request.POST)
        if form.is_valid():
            # Obtener el estado "Cancelada por Admin"
            estado_cancelada = EstadoReserva.objects.get(nombre='Cancelada por Admin')
            reserva.estado = estado_cancelada
            reserva.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
            reserva.save()
            
            messages.success(request, "Reserva cancelada exitosamente.")
            return redirect('admin:reservas_reserva_changelist')
    else:
        form = CancelarReservaForm()
    
    return render(request, 'reservas/admin_cancelar_reserva.html', {
        'form': form,
        'reserva': reserva
    })