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

class Tarjeta(models.Model):
    TIPO_CHOICES = [
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    numero = models.CharField(max_length=16, unique=True)
    vencimiento = models.DateField()
    pin = models.CharField(max_length=3)
    saldo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_tipo_display()} - **** **** **** {self.numero[-4:]}"

    class Meta:
        verbose_name = "Tarjeta"
        verbose_name_plural = "Tarjetas"

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE, null=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.ForeignKey(EstadoReserva, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    dni_conductor = models.CharField(max_length=10, null=True)
    motivo_cancelacion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Reserva de {self.vehiculo} por {self.usuario.username} ({self.fecha_inicio} - {self.fecha_fin})"
    

    def calcular_Total(self):
        # Calcular monto total de la reserva
        if not self.fecha_inicio or not self.fecha_fin:
            return None  
        dias_reserva = (self.fecha_fin - self.fecha_inicio).days + 1
        dias_reserva = max(1, dias_reserva)
        return dias_reserva * self.vehiculo.precio_por_dia


    def calcular_Reembolso(self):
        monto_Total = self.calcular_Total()
        # Calcular el reembolso
        politica = self.vehiculo.politica_reembolso
        porcentaje_reembolso = politica.porcentaje
        return (monto_Total * porcentaje_reembolso) / 100



    def clean(self):
        if self.fecha_inicio is None or self.fecha_fin is None:
            raise ValidationError("Ambas fechas deben estar completas.")
        
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
                estado__nombre__in=['Confirmada'],
            ).exclude(id=self.id)
            
            for reserva in reservas_existentes:
                if (self.fecha_inicio <= reserva.fecha_fin and self.fecha_fin >= reserva.fecha_inicio):
                    raise ValidationError(f"El vehiculo ya esta reservado en el periodo seleccionado. Reserva conflictiva: {reserva}")
                
                
        if hasattr(self, 'dni_conductor') and self.dni_conductor:
            reservas_dni = Reserva.objects.filter(
                dni_conductor=self.dni_conductor,
                estado__nombre='Confirmada'
            ).exclude(id=self.id)  # Excluir la reserva actual (para ediciones)
            
            for reserva in reservas_dni:
                if (self.fecha_inicio <= reserva.fecha_fin and self.fecha_fin >= reserva.fecha_inicio):
                    raise ValidationError(
                        f"El DNI {self.dni_conductor} ya tiene una reserva activa del "
                        f"{reserva.fecha_inicio.strftime('%d/%m/%Y')} al "
                        f"{reserva.fecha_fin.strftime('%d/%m/%Y')} "
                        f"para el vehículo {reserva.vehiculo.marca} {reserva.vehiculo.modelo}. "
                        f"No se pueden tener dos vehículos alquilados simultáneamente."
                    )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    
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

