from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea un perfil para cada usuario nuevo"""
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    instance.perfil.save()