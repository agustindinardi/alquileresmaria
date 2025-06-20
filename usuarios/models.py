from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    # Django ya incluye campos de nombre, apellido, email, etc. en el modelo User
    # Agregamos campos adicionales al perfil
    dni = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    telefono = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

class Empleado(models.Model):
    SUCURSALES_CHOICES = [
        ('Sucursal Central', 'Sucursal Central'),
        ('Sucursal Norte', 'Sucursal Norte'),
        ('Sucursal Sur', 'Sucursal Sur'),
        # Agregar más sucursales según sea necesario
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    sucursal = models.CharField(max_length=50, choices=SUCURSALES_CHOICES, verbose_name="Sucursal")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name} - {self.dni}"
    
    @property
    def edad(self):
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['-fecha_creacion']