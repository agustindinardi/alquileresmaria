from django import forms
from .models import Pago

class PagoTarjetaForm(forms.Form):
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del titular'})
    )
    numero_tarjeta = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numero de tarjeta',
            'pattern': '[0-9]{16}',
            'title': 'Ingrese los 16 digitos de su tarjeta'
        })
    )
    fecha_vencimiento = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/AA',
            'pattern': '(0[1-9]|1[0-2])\/([0-9]{2})',
            'title': 'Formato MM/AA'
        })
    )
    codigo_seguridad = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CVV',
            'pattern': '[0-9]{3,4}',
            'title': 'Codigo de seguridad (3 o 4 digitos)'
        })
    )
    
    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta')
        if not numero.isdigit() or len(numero) != 16:
            raise forms.ValidationError("El numero de tarjeta debe contener 16 digitos.")
        return numero
    
    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get('fecha_vencimiento')
        try:
            mes, anio = fecha.split('/')
            mes = int(mes)
            anio = int('20' + anio)
            
            import datetime
            now = datetime.datetime.now()
            
            if anio < now.year or (anio == now.year and mes < now.month):
                raise forms.ValidationError("La tarjeta ha expirado.")
            
            if not (1 <= mes <= 12):
                raise forms.ValidationError("Mes invalido.")
                
        except ValueError:
            raise forms.ValidationError("Formato de fecha invalido. Use MM/AA.")
            
        return fecha
    
    def clean_codigo_seguridad(self):
        codigo = self.cleaned_data.get('codigo_seguridad')
        if not codigo.isdigit() or not (3 <= len(codigo) <= 4):
            raise forms.ValidationError("El codigo de seguridad debe contener 3 o 4 digitos.")
        return codigo