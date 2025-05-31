from django import forms
from .models import Reserva
from django.utils import timezone

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.vehiculo = kwargs.pop('vehiculo', None)
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            # Validar que la fecha de inicio sea posterior a la fecha actual
            if fecha_inicio < timezone.now().date():
                self.add_error('fecha_inicio', "La fecha de inicio debe ser posterior a la fecha actual.")
            
            # Validar que la fecha de fin sea posterior a la fecha de inicio
            if fecha_fin < fecha_inicio:
                self.add_error('fecha_fin', "La fecha de fin debe ser posterior a la fecha de inicio.")
            
            # Validar que el vehiculo no este reservado en las fechas seleccionadas
            from .models import Reserva
            reservas_existentes = Reserva.objects.filter(
                vehiculo=self.vehiculo,
                estado__nombre__in=['Pendiente', 'Confirmada'],
            )
            
            for reserva in reservas_existentes:
                if (fecha_inicio <= reserva.fecha_fin and fecha_fin >= reserva.fecha_inicio):
                    self.add_error(None, f"El vehiculo ya esta reservado en el periodo seleccionado.")
                    break
        
        return cleaned_data

class CancelarReservaForm(forms.Form):
    motivo_cancelacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )