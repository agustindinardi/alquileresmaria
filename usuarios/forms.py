from django import forms
from django.contrib.auth.models import User
from .models import Perfil
from django.contrib.auth.forms import UserCreationForm
from datetime import date

# Formulario para el registro de usuarios de Django
class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) > 8:
            raise forms.ValidationError("La contraseña no puede tener más de 8 caracteres.")
        return password
    
# Formulario para el perfil de usuario 
class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['dni', 'fecha_nacimiento', 'telefono']

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento is None:
            return fecha_nacimiento  # No hagas nada si está vacío, dejará que el validador por defecto actúe
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        if edad < 18:
            raise forms.ValidationError("Debes ser mayor de 18 años para registrarte.")
        return fecha_nacimiento