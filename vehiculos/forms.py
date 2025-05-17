from django import forms
from .models import Vehiculo

# class BusquedaVehiculoForm(forms.Form):
#     fecha_inicio = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         required=True
#     )
#     fecha_fin = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         required=True
#     )
#     tipo = forms.ModelChoiceField(
#         queryset=None,
#         required=False,
#         empty_label="Todos los tipos",
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )
#     marca = forms.ModelChoiceField(
#         queryset=None,
#         required=False,
#         empty_label="Todas las marcas",
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )
#     capacidad_minima = forms.IntegerField(
#         required=False,
#         min_value=1,
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Capacidad minima'})
#     )
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     from .models import TipoVehiculo, Marca
    #     self.fields['tipo'].queryset = TipoVehiculo.objects.all()
    #     self.fields['marca'].queryset = Marca.objects.all()

class VehiculoForm(forms.ModelForm):
    """Formulario para la creación y edición de vehículos."""
    
    class Meta:
        model = Vehiculo
        fields = [
            'marca', 'tipo', 'modelo', 'ano', 'patente', 
            'capacidad', 'precio_por_dia', 'kilometraje',
            'politica_reembolso', 'descripcion', 'imagen', 'disponible',
            'sucursal'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio_por_dia': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'kilometraje': forms.NumberInput(attrs={'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar los labels y ayudas
        self.fields['precio_por_dia'].label = 'Precio por día ($)'
        self.fields['ano'].label = 'Año'
        self.fields['disponible'].help_text = 'Marcar si el vehículo está disponible para alquiler'
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