from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Perfil, Empleado
from django.contrib.auth.forms import UserCreationForm
from datetime import date

# Formulario para el registro de usuarios de Django
class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = 'required'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electronico ya esta registrado.")
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) > 8:
            raise forms.ValidationError("La contraseña no puede tener más de 8 caracteres.")
        return password

    def save(self, commit=True):    # De esta forma tomamos el email como username
        user = super().save(commit=False)
        email = self.cleaned_data.get('email')
        # Generamos un username basado en el email (único)
        user.username = email
        if commit:
            user.save()
        return user
    
# Formulario para el perfil de usuario 
class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['dni', 'fecha_nacimiento', 'telefono']
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                format='%d-%m-%Y',
                attrs={'type': 'date', 'max': date.today().isoformat()}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = 'required'
            self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento is None:
            return fecha_nacimiento  # No hagas nada si está vacío, dejará que el validador por defecto actúe
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        if edad < 18:
            raise forms.ValidationError("Debes ser mayor de 18 años para registrarte.")
        return fecha_nacimiento
      
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Perfil.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado.")
        if not dni.isdigit():
            raise forms.ValidationError("El DNI debe contener solo números.")
        return dni

# Formulario para crear empleado
class EmpleadoForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'required'})
    )
    last_name = forms.CharField(
        max_length=30,
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': 'required'})
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'})
    )
    
    class Meta:
        model = Empleado
        fields = ['dni', 'fecha_nacimiento', 'sucursal']
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}
            ),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'sucursal': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
        }
        labels = {
            'dni': 'DNI',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'sucursal': 'Sucursal',
        }

    def __init__(self, *args, **kwargs):
        self.instance_pk = kwargs.pop('instance_pk', None)
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, llenar los campos del usuario
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        
        # Validar que solo contenga números
        if not dni.isdigit():
            raise forms.ValidationError("El DNI debe contener solo números.")
        
        # Validar que el DNI sea único (excepto para el empleado actual en edición)
        existing_empleado = Empleado.objects.filter(dni=dni).first()
        if existing_empleado:
            if not self.instance or existing_empleado.pk != self.instance.pk:
                raise forms.ValidationError("El Empleado ya se encuentra registrado.")
        
        # También verificar en Perfil para evitar conflictos
        if Perfil.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado en el sistema.")
        
        return dni

    def clean_email(self):
        email = self.cleaned_data.get('email')

        existing_user = User.objects.filter(email=email).first()
        
        # Verificamos si la instancia tiene asignado un usuario antes de comparar
        if existing_user:
            if not self.instance.pk or not hasattr(self.instance, 'usuario') or existing_user != getattr(self.instance, 'usuario', None):
                raise forms.ValidationError("Este correo electrónico ya está registrado.")

        return email


    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if fecha_nacimiento is None:
            return fecha_nacimiento
        
        # Calcular edad
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        
        if edad < 18:
            raise forms.ValidationError("El Empleado no puede registrarse ya que no cumple con el limite de edad.")
        
        return fecha_nacimiento

#Formulario para loguearse
class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electrónico")

#Formulario para recuperar contraseña
class RecuperarContrasenaForm(forms.Form):
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu correo',
            'required': 'required'
        })
    )

#Formulario para validar código de seguridad
class CodigoValidacionForm(forms.Form):
    codigo = forms.CharField(
        label="Código de Seguridad",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1234-A',
            'required': 'required',
            'pattern': '[0-9]{4}-[A-Z]',
            'title': 'Formato: 1234-A'
        })
    )
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper().strip()
            # Validar formato XXXX-X
            import re
            if not re.match(r'^\d{4}-[A-Z]$', codigo):
                raise forms.ValidationError("El código debe tener el formato 1234-A")
        return codigo