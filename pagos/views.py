from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PagoTarjetaForm
from .models import Pago, MetodoPago
from reservas.models import Reserva, EstadoReserva
from django.urls import reverse

@login_required
def procesar_pago(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    
    # Calcular el monto total
    monto_total = reserva.calcular_total()
    
    if request.method == 'POST':
        form = PagoTarjetaForm(request.POST)
        if form.is_valid():
            # Simular procesamiento de pago
            # En un entorno real, aqui se integraria con un gateway de pagos
            
            # Registrar el pago
            metodo_pago = MetodoPago.objects.get(nombre='Tarjeta de Credito/Debito')
            pago = Pago(
                reserva=reserva,
                metodo_pago=metodo_pago,
                monto=monto_total,
                referencia_pago=f"REF-{reserva.id}-{request.user.id}"
            )
            pago.save()
            
            # Actualizar estado de la reserva
            estado_confirmada = EstadoReserva.objects.get(nombre='Confirmada')
            reserva.estado = estado_confirmada
            reserva.save()
            
            messages.success(request, "Pago procesado exitosamente. Su reserva ha sido confirmada.")
            return redirect('reservas:detalle', pk=reserva.id)
    else:
        form = PagoTarjetaForm()
    
    return render(request, 'pagos/procesar_pago.html', {
        'form': form,
        'reserva': reserva,
        'monto_total': monto_total
    })

@login_required
def historial_pagos(request):
    # Obtener todos los pagos del usuario
    pagos = Pago.objects.filter(reserva__usuario=request.user).order_by('-fecha_pago')
    
    return render(request, 'pagos/historial_pagos.html', {
        'pagos': pagos
    })