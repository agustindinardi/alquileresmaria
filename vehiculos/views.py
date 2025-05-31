from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, JsonResponse
from django.db import IntegrityError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q

from .models import Vehiculo, Marca, TipoVehiculo, PoliticaReembolso, Sucursal, Estado
from .forms import VehiculoForm, VehiculoEstadoForm, BusquedaVehiculoForm
from reservas.models import Reserva  # Asegurate que esta importación sea correcta según tu estructura


# Función auxiliar para comprobar si el usuario es staff
def es_staff(user):
    return user.is_staff

def home_view(request):
    """Vista para la página de inicio con formulario de búsqueda."""
    # Pasar información de si es staff al formulario
    form = BusquedaVehiculoForm(is_staff=request.user.is_staff)
    
    if request.method == 'POST':
        form = BusquedaVehiculoForm(request.POST, is_staff=request.user.is_staff)
        if form.is_valid():
            # Construir URL con parámetros de búsqueda
            params = []
            
            if form.cleaned_data['fecha_entrega']:
                params.append(f"fecha_entrega={form.cleaned_data['fecha_entrega']}")
            
            if form.cleaned_data['fecha_devolucion']:
                params.append(f"fecha_devolucion={form.cleaned_data['fecha_devolucion']}")
            
            if form.cleaned_data['sucursal']:
                params.append(f"sucursal={form.cleaned_data['sucursal'].id}")
            
            if form.cleaned_data['categoria']:
                params.append(f"tipo={form.cleaned_data['categoria'].id}")
            
            if form.cleaned_data['capacidad']:
                params.append(f"capacidad={form.cleaned_data['capacidad']}")
            
            if form.cleaned_data['kilometraje']:
                params.append(f"kilometraje={form.cleaned_data['kilometraje']}")
            
            # Redirigir a la lista de vehículos con los filtros
            url = reverse('vehiculos:lista')
            if params:
                url += '?' + '&'.join(params)
            
            return redirect(url)
    
    context = {
        'form': form,
    }
    return render(request, 'home.html', context)

class VehiculoListView(ListView):
    """Vista para listar todos los vehículos."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_list.html'
    context_object_name = 'vehiculos'
    paginate_by = 9  # Mostrar 9 vehículos por página

    def get_queryset(self):
        """Personalizar la consulta para filtrar los vehículos."""
        queryset = super().get_queryset()
        
        # Filtros de búsqueda por disponibilidad en fechas
        fecha_entrega = self.request.GET.get('fecha_entrega')
        fecha_devolucion = self.request.GET.get('fecha_devolucion')
        
        # Solo aplicar filtro de fechas si ambas están presentes
        if fecha_entrega and fecha_devolucion:
            # Importar aquí para evitar importación circular
            from reservas.models import Reserva
            
            # Obtener vehículos que NO tienen reservas en el rango de fechas
            reservas_conflictivas = Reserva.objects.filter(
                Q(fecha_inicio__lte=fecha_devolucion) & Q(fecha_fin__gte=fecha_entrega),
                estado__nombre__in=['Confirmada', 'Activa']  # Solo reservas activas
            ).values_list('vehiculo_id', flat=True)
            
            queryset = queryset.exclude(id__in=reservas_conflictivas)
            
            # Solo mostrar vehículos disponibles (no en mantenimiento) cuando se filtran por fechas
            try:
                estado_disponible = Estado.objects.get(nombre__iexact='disponible')
                queryset = queryset.filter(estado=estado_disponible)
            except Estado.DoesNotExist:
                pass
        
        # Si no es staff y no hay filtros de fecha, mostrar solo disponibles por defecto
        elif not self.request.user.is_staff:
            try:
                estado_disponible = Estado.objects.get(nombre__iexact='disponible')
                queryset = queryset.filter(estado=estado_disponible)
            except Estado.DoesNotExist:
                pass
        
        # Filtrar por estado usando el nombre del estado
        estado_nombre = self.request.GET.get('estado')
        if estado_nombre:
            try:
                estado = Estado.objects.get(nombre__iexact=estado_nombre)
                queryset = queryset.filter(estado=estado)
            except Estado.DoesNotExist:
                pass
        
        # Mantener compatibilidad con filtro de disponibilidad
        disponible = self.request.GET.get('disponible')
        if disponible == 'true':
            try:
                estado_disponible = Estado.objects.get(nombre__iexact='disponible')
                queryset = queryset.filter(estado=estado_disponible)
            except Estado.DoesNotExist:
                pass
        elif disponible == 'false':
            try:
                estado_disponible = Estado.objects.get(nombre__iexact='disponible')
                queryset = queryset.exclude(estado=estado_disponible)
            except Estado.DoesNotExist:
                pass
            
        # CAMBIO: Filtrar por marca usando búsqueda de texto en el campo marca del vehículo
        marca_texto = self.request.GET.get('marca')
        if marca_texto and marca_texto.strip():
            # Búsqueda insensible a mayúsculas y minúsculas que contenga el texto
            queryset = queryset.filter(marca__icontains=marca_texto.strip())
            
        # Filtrar por tipo/categoría (si se especifica en la URL)
        tipo_id = self.request.GET.get('tipo')
        if tipo_id:
            queryset = queryset.filter(tipo_id=tipo_id)
            
        # Filtrar por sucursal (si se especifica en la URL)
        sucursal_id = self.request.GET.get('sucursal')
        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)
        
        # Filtrar por capacidad
        capacidad = self.request.GET.get('capacidad')
        if capacidad:
            if capacidad == '8':  # 8+ pasajeros
                queryset = queryset.filter(capacidad__gte=8)
            else:
                queryset = queryset.filter(capacidad=capacidad)
        
        # Filtrar por kilometraje
        kilometraje = self.request.GET.get('kilometraje')
        if kilometraje:
            if kilometraje == '0':
                queryset = queryset.filter(kilometraje=0)
            else:
                queryset = queryset.filter(kilometraje__lt=int(kilometraje))
            
        return queryset

    def get_context_data(self, **kwargs):
        """Añadir datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        # CAMBIO: Ya no necesitamos pasar las marcas del modelo Marca
        # context['marcas'] = Marca.objects.all()  # Comentado o eliminado
        context['tipos'] = TipoVehiculo.objects.all()
        context['sucursales'] = Sucursal.objects.all()
        context['estados'] = Estado.objects.all()
        
        # Formulario de búsqueda con datos actuales
        initial_data = {}
        if self.request.GET.get('fecha_entrega'):
            initial_data['fecha_entrega'] = self.request.GET.get('fecha_entrega')
        if self.request.GET.get('fecha_devolucion'):
            initial_data['fecha_devolucion'] = self.request.GET.get('fecha_devolucion')
        if self.request.GET.get('sucursal'):
            try:
                initial_data['sucursal'] = Sucursal.objects.get(id=self.request.GET.get('sucursal'))
            except (Sucursal.DoesNotExist, ValueError):
                pass
        if self.request.GET.get('tipo'):
            try:
                initial_data['categoria'] = TipoVehiculo.objects.get(id=self.request.GET.get('tipo'))
            except (TipoVehiculo.DoesNotExist, ValueError):
                pass
        if self.request.GET.get('capacidad'):
            initial_data['capacidad'] = self.request.GET.get('capacidad')
        if self.request.GET.get('kilometraje'):
            initial_data['kilometraje'] = self.request.GET.get('kilometraje')
        # CAMBIO: Agregar el valor de marca como texto
        if self.request.GET.get('marca'):
            initial_data['marca_texto'] = self.request.GET.get('marca')
        
        # Pasar información de si es staff al formulario
        context['busqueda_form'] = BusquedaVehiculoForm(
            initial=initial_data, 
            is_staff=self.request.user.is_staff
        )
        
        # Información de búsqueda activa
        context['busqueda_activa'] = bool(
            self.request.GET.get('fecha_entrega') or 
            self.request.GET.get('fecha_devolucion') or
            self.request.GET.get('sucursal') or
            self.request.GET.get('tipo') or
            self.request.GET.get('capacidad') or
            self.request.GET.get('kilometraje') or
            self.request.GET.get('marca') or  # CAMBIO: Incluir marca en búsqueda activa
            self.request.GET.get('disponible')
        )
        
        # Estadísticas de estados
        stats = {'total': Vehiculo.objects.count()}
        
        # Contar vehículos por cada estado existente
        for estado in Estado.objects.all():
            estado_key = estado.nombre.lower().replace(' ', '_')
            stats[estado_key] = Vehiculo.objects.filter(estado=estado).count()
        
        # Mantener compatibilidad con nombres específicos si existen
        try:
            disponible_estado = Estado.objects.get(nombre__iexact='disponible')
            stats['disponibles'] = Vehiculo.objects.filter(estado=disponible_estado).count()
        except Estado.DoesNotExist:
            stats['disponibles'] = 0
            
        try:
            reservado_estado = Estado.objects.get(nombre__iexact='reservado')
            stats['reservados'] = Vehiculo.objects.filter(estado=reservado_estado).count()
        except Estado.DoesNotExist:
            stats['reservados'] = 0
            
        try:
            mantenimiento_estado = Estado.objects.get(nombre__iexact='mantenimiento')
            stats['mantenimiento'] = Vehiculo.objects.filter(estado=mantenimiento_estado).count()
        except Estado.DoesNotExist:
            stats['mantenimiento'] = 0
        
        context['stats'] = stats
        
        return context

class VehiculoDetailView(DetailView):
    """Vista para ver los detalles de un vehículo específico."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_detail.html'
    context_object_name = 'vehiculo'

    def get_context_data(self, **kwargs):
        """Añadir datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Agregar formulario para cambio de estado si el usuario es staff
        if self.request.user.is_staff:
            context['estado_form'] = VehiculoEstadoForm(instance=self.object)
            context['estados_disponibles'] = Estado.objects.all()
        
        return context

class VehiculoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vista para crear un nuevo vehículo (solo staff)."""
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'vehiculos/vehiculo_form.html'
    success_url = reverse_lazy('vehiculos:lista')

    def test_func(self):
        """Comprobar si el usuario tiene permisos para crear vehículos."""
        return self.request.user.is_staff

    def form_valid(self, form):
        """Procesar el formulario cuando es válido."""
        try:
            # Intenta guardar el formulario
            response = super().form_valid(form)
            # Si todo va bien, mostrar mensaje de éxito
            estado_display = self.object.estado.nombre if self.object.estado else 'Sin estado'
            messages.success(
                self.request, 
                f'¡Vehículo {self.object.marca} {self.object.modelo} con patente {self.object.patente} '
                f'creado correctamente! Estado: {estado_display}'
            )
            return response
        except IntegrityError as e:
            # Si hay un error de integridad (patente duplicada), mostrarlo
            if 'unique constraint' in str(e).lower() and 'patente' in str(e).lower():
                form.add_error('patente', f'Ya existe un vehículo con la patente {form.cleaned_data["patente"]} en el sistema.')
            else:
                form.add_error(None, f'Error al guardar el vehículo: {str(e)}')
            return self.form_invalid(form)

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
        # Redirigir a la lista con filtros vacíos
        return reverse('vehiculos:lista') + '?marca=&tipo=&sucursal=&disponible='

    def form_valid(self, form):
        """Procesar el formulario cuando es válido."""
        try:
            response = super().form_valid(form)
            messages.success(self.request, f'¡Vehículo {self.object.marca} {self.object.modelo} actualizado correctamente!')
            return response
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower() and 'patente' in str(e).lower():
                form.add_error('patente', f'Ya existe un vehículo con la patente {form.cleaned_data["patente"]} en el sistema.')
            else:
                form.add_error(None, f'Error al actualizar el vehículo: {str(e)}')
            return self.form_invalid(form)

class VehiculoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vista para eliminar un vehículo (solo staff)."""
    model = Vehiculo
    template_name = 'vehiculos/vehiculo_confirm_delete.html' 
    success_url = reverse_lazy('vehiculos:lista')
    context_object_name = 'vehiculo'

    def test_func(self):
        """Comprobar si el usuario tiene permisos para eliminar vehículos."""
        return self.request.user.is_staff

    # def delete(self, request, *args, **kwargs):
    def post(self, request, *args, **kwargs):
        """Personalizar el proceso de eliminación."""
        vehiculo = self.get_object()

        # Verificar si el vehículo está reservado
        # if vehiculo.esta_reservado():   jeje ta bien
        if Reserva.objects.filter(vehiculo=vehiculo, motivo_cancelacion__isnull=True).exists():
            messages.error(
                request, 
                f'No se puede eliminar el vehículo {vehiculo.marca} {vehiculo.modelo} '
                f'porque está actualmente reservado.'
            )
            return redirect('/vehiculos/')
        
        estado_display = vehiculo.estado.nombre if vehiculo.estado else 'Sin estado'
        messages.success(
            request, 
            f'El vehículo {vehiculo.marca} {vehiculo.modelo} ({estado_display}) ha sido eliminado.'
        )
        return super().delete(request, *args, **kwargs)
