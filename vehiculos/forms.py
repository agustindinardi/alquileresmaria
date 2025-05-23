from django import forms
from .models import Vehiculo

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Marca, TipoVehiculo, Sucursal
        
        self.fields['marca'].queryset = Marca.objects.all()
        self.fields['tipo'].queryset = TipoVehiculo.objects.all()
        self.fields['sucursal'].queryset = Sucursal.objects.all()