# from django.shortcuts import render, get_object_or_404
# from django.views.generic import ListView, DetailView
# from .models import Vehiculo, TipoVehiculo, Marca
# from .forms import BusquedaVehiculoForm
# from reservas.models import Reserva
# from django.db.models import Q

# class VehiculoListView(ListView):
#     model = Vehiculo
#     template_name = 'vehiculos/vehiculo_list.html'
#     context_object_name = 'vehiculos'
#     paginate_by = 9
    
#     def get_queryset(self):
#         queryset = Vehiculo.objects.filter(disponible=True)
        
#         # Aplicar filtros de busqueda
#         form = BusquedaVehiculoForm(self.request.GET)
#         if form.is_valid():
#             fecha_inicio = form.cleaned_data.get('fecha_inicio')
#             fecha_fin = form.cleaned_data.get('fecha_fin')
#             tipo = form.cleaned_data.get('tipo')
#             marca = form.cleaned_data.get('marca')
#             capacidad_minima = form.cleaned_data.get('capacidad_minima')
            
#             # Filtrar por tipo de vehiculo
#             if tipo:
#                 queryset = queryset.filter(tipo=tipo)
            
#             # Filtrar por marca
#             if marca:
#                 queryset = queryset.filter(marca=marca)
            
#             # Filtrar por capacidad minima
#             if capacidad_minima:
#                 queryset = queryset.filter(capacidad__gte=capacidad_minima)
            
#             # Filtrar vehiculos disponibles en el rango de fechas
#             if fecha_inicio and fecha_fin:
#                 # Obtener IDs de vehiculos con reservas en el rango de fechas
#                 reservas = Reserva.objects.filter(
#                     Q(fecha_inicio__lte=fecha_fin) & Q(fecha_fin__gte=fecha_inicio),
#                     estado__nombre__in=['Pendiente', 'Confirmada']
#                 ).values_list('vehiculo_id', flat=True)
                
#                 # Excluir vehiculos con reservas en el rango de fechas
#                 queryset = queryset.exclude(id__in=reservas)
        
#         return queryset
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['form'] = BusquedaVehiculoForm(self.request.GET)
#         return context

# class VehiculoDetailView(DetailView):
#     model = Vehiculo
#     template_name = 'vehiculos/vehiculo_detail.html'
#     context_object_name = 'vehiculo'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Anadir formulario de reserva
#         from reservas.forms import ReservaForm
#         context['form'] = ReservaForm(vehiculo=self.object, usuario=self.request.user)
#         return context

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from .models import Vehiculo, Marca, TipoVehiculo, PoliticaReembolso
from .forms import VehiculoForm

# Función auxiliar para comprobar si el usuario es staff
def es_staff(user):
    return user.is_staff

class VehiculoListView(ListView):
    """Vista para listar todos los vehículos."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 9  # Mostrar 9 vehículos por página
    
    def get_queryset(self):
        """Personalizar la consulta para filtrar los vehículos."""
        queryset = super().get_queryset()
        
        # Filtrar por disponibilidad (si se especifica en la URL)
        disponible = self.request.GET.get('disponible')
        if disponible == 'true':
            queryset = queryset.filter(disponible=True)
        elif disponible == 'false':
            queryset = queryset.filter(disponible=False)
            
        # Filtrar por marca (si se especifica en la URL)
        marca_id = self.request.GET.get('marca')
        if marca_id:
            queryset = queryset.filter(marca_id=marca_id)
            
        # Filtrar por tipo (si se especifica en la URL)
        tipo_id = self.request.GET.get('tipo')
        if tipo_id:
            queryset = queryset.filter(tipo_id=tipo_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Añadir datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        context['marcas'] = Marca.objects.all()
        context['tipos'] = TipoVehiculo.objects.all()
        return context

class VehiculoDetailView(DetailView):
    """Vista para ver los detalles de un vehículo específico."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_detail.html'
    context_object_name = 'vehiculo'

class VehiculoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vista para crear un nuevo vehículo (solo staff)."""
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculo-list')
    
    def test_func(self):
        """Comprobar si el usuario tiene permisos para crear vehículos."""
        return self.request.user.is_staff
    
    def form_valid(self, form):
        """Procesar el formulario cuando es válido."""
        messages.success(self.request, f'¡Vehículo creado correctamente!')
        return super().form_valid(form)

class VehiculoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vista para actualizar un vehículo existente (solo staff)."""
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    
    def test_func(self):
        """Comprobar si el usuario tiene permisos para actualizar vehículos."""
        return self.request.user.is_staff
    
    def get_success_url(self):
        """URL a la que redirigir tras actualizar con éxito."""
        return reverse('vehiculo-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Procesar el formulario cuando es válido."""
        messages.success(self.request, f'¡Vehículo actualizado correctamente!')
        return super().form_valid(form)

class VehiculoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vista para eliminar un vehículo (solo staff)."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_confirm_delete.html'
    success_url = reverse_lazy('vehiculo-list')
    context_object_name = 'vehiculo'
    
    def test_func(self):
        """Comprobar si el usuario tiene permisos para eliminar vehículos."""
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        """Personalizar el proceso de eliminación."""
        vehiculo = self.get_object()
        messages.success(request, f'El vehículo {vehiculo.marca} {vehiculo.modelo} ha sido eliminado.')
        return super().delete(request, *args, **kwargs)
    
