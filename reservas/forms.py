from django import forms
from .models import Reserva, Tarjeta
from django.utils import timezone

class ReservaForm(forms.ModelForm):

    numero_tarjeta = forms.CharField(
        label="Número de Tarjeta",
        max_length=16,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    pin_tarjeta = forms.CharField(
        label="PIN",
        max_length=3,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    vencimiento_tarjeta = forms.DateField(
        label="Fecha de Vencimiento",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

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
        numero_tarjeta = cleaned_data.get('numero_tarjeta')
        pin_tarjeta = cleaned_data.get('pin_tarjeta')
        vencimiento_input = cleaned_data.get('vencimiento_tarjeta')
        
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
                estado__nombre__in=['Cancelada', 'Confirmada'],
            )
            
            for reserva in reservas_existentes:
                if (fecha_inicio <= reserva.fecha_fin and fecha_fin >= reserva.fecha_inicio):
                    self.add_error(None, f"El vehiculo ya esta reservado en el periodo seleccionado.")
                    break
        
        
         # Validación de tarjeta
        try:
            tarjeta = Tarjeta.objects.get(numero=numero_tarjeta)
        except Tarjeta.DoesNotExist:
            self.add_error('numero_tarjeta', "El número de tarjeta no es válido.")
            return cleaned_data

        if tarjeta.pin != pin_tarjeta:
            self.add_error('pin_tarjeta', "El PIN ingresado no es correcto.")

        if tarjeta.vencimiento != vencimiento_input:
            self.add_error('vencimiento_tarjeta', "La fecha de vencimiento no coincide con la tarjeta.")

        if tarjeta.vencimiento < timezone.now().date():
            self.add_error('vencimiento_tarjeta', "La tarjeta está vencida.")

        # Verificar saldo
        if fecha_inicio and fecha_fin:
            dias = (fecha_fin - fecha_inicio).days + 1
            total = dias * self.vehiculo.precio_por_dia
            if tarjeta.saldo < total:
                self.add_error(None, "La tarjeta no tiene saldo suficiente para realizar la reserva.")


        return cleaned_data

class CancelarReservaForm(forms.Form):
    motivo_cancelacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )