from django import forms
from .models import Vehiculo, TipoVehiculo, Sucursal
from django.core.exceptions import ValidationError
from datetime import date


class VehiculoForm(forms.ModelForm):
    """Formulario para la creación y edición de vehículos."""
    
    class Meta:
        model = Vehiculo
        fields = [
            'marca', 'tipo', 'modelo', 'ano', 'patente', 
            'capacidad', 'precio_por_dia', 'kilometraje',
            'politica_reembolso', 'descripcion', 'imagen', 'estado',
            'sucursal'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio_por_dia': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'kilometraje': forms.NumberInput(attrs={'min': '0'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar los labels y ayudas
        self.fields['precio_por_dia'].label = 'Precio por día ($)'
        self.fields['ano'].label = 'Año'
        self.fields['estado'].label = 'Estado del vehículo'
        self.fields['estado'].help_text = 'Estado actual del vehículo (Disponible, Reservado, En Mantenimiento)'
        self.fields['sucursal'].label = 'Sucursal'
        
        # Hacer que algunos campos sean obligatorios
        for campo in ['marca', 'tipo', 'modelo', 'ano', 'patente', 'capacidad', 'precio_por_dia', 'kilometraje', 'sucursal']:
            self.fields[campo].required = True
    
    def clean_patente(self):
        """Validar que la patente no exista ya en el sistema."""
        patente = self.cleaned_data.get('patente')
        
        # Verificar si la patente ya existe en otro vehículo
        if Vehiculo.objects.filter(patente=patente).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Ya existe un vehículo con esta patente en el sistema.")
            
        return patente

class VehiculoEstadoForm(forms.ModelForm):
    """Formulario simplificado para cambiar solo el estado de un vehículo."""
    
    class Meta:
        model = Vehiculo
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].label = 'Nuevo estado'
        self.fields['estado'].help_text = 'Seleccione el nuevo estado para el vehículo'

class BusquedaVehiculoForm(forms.Form):
    """Formulario para búsqueda de vehículos con filtros de disponibilidad."""
    
    KILOMETRAJE_CHOICES = [
        ('', 'Cualquier kilometraje'),
        ('0', '0 km (Nuevos)'),
        ('50000', 'Menos de 50,000 km'),
        ('100000', 'Menos de 100,000 km'),
        ('150000', 'Menos de 150,000 km'),
    ]
    
    fecha_entrega = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().strftime('%Y-%m-%d')
        }),
        label='Fecha de entrega',
        required=True  # Se modificará en __init__ según el usuario
    )
    
    fecha_devolucion = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha de devolución',
        required=True  # Se modificará en __init__ según el usuario
    )
    
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.all(),
        empty_label='Todas las sucursales',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Sucursal',
        required=False
    )
    
    categoria = forms.ModelChoiceField(
        queryset=TipoVehiculo.objects.all(),
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Categoría',
        required=False
    )
    
    capacidad = forms.ChoiceField(
        choices=[
            ('', 'Cualquier capacidad'),
            ('2', '2 pasajeros'),
            ('4', '4 pasajeros'),
            ('5', '5 pasajeros'),
            ('7', '7 pasajeros'),
            ('8', '8+ pasajeros'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Capacidad',
        required=False
    )
    
    kilometraje = forms.ChoiceField(
        choices=KILOMETRAJE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Kilometraje máximo',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        # Extraer el parámetro is_staff si existe
        is_staff = kwargs.pop('is_staff', False)
        super().__init__(*args, **kwargs)
        
        # Si es staff, las fechas no son obligatorias
        if is_staff:
            self.fields['fecha_entrega'].required = False
            self.fields['fecha_devolucion'].required = False
            self.fields['fecha_entrega'].label = 'Fecha de entrega (opcional)'
            self.fields['fecha_devolucion'].label = 'Fecha de devolución (opcional)'
            self.fields['fecha_entrega'].help_text = 'Opcional para administradores'
            self.fields['fecha_devolucion'].help_text = 'Opcional para administradores'
            
            # Remover la fecha mínima para administradores
            self.fields['fecha_entrega'].widget.attrs.pop('min', None)
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_entrega = cleaned_data.get('fecha_entrega')
        fecha_devolucion = cleaned_data.get('fecha_devolucion')
        
        # Solo validar fechas si ambas están presentes
        if fecha_entrega and fecha_devolucion:
            # Validar que la fecha de devolución sea posterior a la fecha de entrega
            if fecha_devolucion <= fecha_entrega:
                raise ValidationError('La fecha de devolución debe ser posterior a la fecha de entrega.')
        
        # Para usuarios no-staff, validar que la fecha de entrega no sea en el pasado
        # Solo si la fecha está presente
        if fecha_entrega and not getattr(self, '_is_staff', False):
            if fecha_entrega < date.today():
                raise ValidationError('La fecha de entrega no puede ser en el pasado.')
        
        return cleaned_data
