from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Vehiculo, TipoVehiculo, Marca
from .forms import BusquedaVehiculoForm
from reservas.models import Reserva
from django.db.models import Q

class VehiculoListView(ListView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Vehiculo.objects.filter(disponible=True)
        
        # Aplicar filtros de busqueda
        form = BusquedaVehiculoForm(self.request.GET)
        if form.is_valid():
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')
            tipo = form.cleaned_data.get('tipo')
            marca = form.cleaned_data.get('marca')
            capacidad_minima = form.cleaned_data.get('capacidad_minima')
            
            # Filtrar por tipo de vehiculo
            if tipo:
                queryset = queryset.filter(tipo=tipo)
            
            # Filtrar por marca
            if marca:
                queryset = queryset.filter(marca=marca)
            
            # Filtrar por capacidad minima
            if capacidad_minima:
                queryset = queryset.filter(capacidad__gte=capacidad_minima)
            
            # Filtrar vehiculos disponibles en el rango de fechas
            if fecha_inicio and fecha_fin:
                # Obtener IDs de vehiculos con reservas en el rango de fechas
                reservas = Reserva.objects.filter(
                    Q(fecha_inicio__lte=fecha_fin) & Q(fecha_fin__gte=fecha_inicio),
                    estado__nombre__in=['Pendiente', 'Confirmada']
                ).values_list('vehiculo_id', flat=True)
                
                # Excluir vehiculos con reservas en el rango de fechas
                queryset = queryset.exclude(id__in=reservas)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BusquedaVehiculoForm(self.request.GET)
        return context

class VehiculoDetailView(DetailView):
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_detail.html'
    context_object_name = 'vehiculo'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Anadir formulario de reserva
        from reservas.forms import ReservaForm
        context['form'] = ReservaForm(vehiculo=self.object, usuario=self.request.user)
        return context