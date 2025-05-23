from django.db import models
from django.contrib.auth.models import User
from vehiculos.models import Vehiculo
from django.core.exceptions import ValidationError
from django.utils import timezone

class EstadoReserva(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Estado de Reserva"
        verbose_name_plural = "Estados de Reservas"

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.ForeignKey(EstadoReserva, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    motivo_cancelacion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Reserva de {self.vehiculo} por {self.usuario.username} ({self.fecha_inicio} - {self.fecha_fin})"
    
    def clean(self):
        # Validar que la fecha de inicio sea posterior a la fecha actual
        if self.fecha_inicio < timezone.now().date():
            raise ValidationError("La fecha de inicio debe ser posterior a la fecha actual.")
        
        # Validar que la fecha de fin sea posterior a la fecha de inicio
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")
        
        # Validar que el vehiculo no este reservado en las fechas seleccionadas
        # Solo si tenemos un vehículo asignado
        if hasattr(self, 'vehiculo') and self.vehiculo:
            reservas_existentes = Reserva.objects.filter(
                vehiculo=self.vehiculo,
                estado__nombre__in=['Cancelada', 'Confirmada'],
            ).exclude(id=self.id)
            
            for reserva in reservas_existentes:
                if (self.fecha_inicio <= reserva.fecha_fin and self.fecha_fin >= reserva.fecha_inicio):
                    raise ValidationError(f"El vehiculo ya esta reservado en el periodo seleccionado. Reserva conflictiva: {reserva}")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Calcula el costo total de la reserva"""
        dias = (self.fecha_fin - self.fecha_inicio).days + 1
        return dias * self.vehiculo.tarifa_diaria
    
    def puede_cancelar_usuario(self):
        """Verifica si el usuario puede cancelar la reserva (24 horas antes)"""
        horas_limite = 24
        ahora = timezone.now()
        inicio_reserva = timezone.make_aware(timezone.datetime.combine(self.fecha_inicio, timezone.datetime.min.time()))
        return (inicio_reserva - ahora).total_seconds() / 3600 >= horas_limite
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_creacion']