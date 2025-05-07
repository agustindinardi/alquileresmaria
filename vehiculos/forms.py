from django import forms
from .models import Vehiculo

class BusquedaVehiculoForm(forms.Form):
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    tipo = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    marca = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Todas las marcas",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    capacidad_minima = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Capacidad minima'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import TipoVehiculo, Marca
        self.fields['tipo'].queryset = TipoVehiculo.objects.all()
        self.fields['marca'].queryset = Marca.objects.all()