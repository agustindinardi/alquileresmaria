from django.db import models
from reservas.models import Reserva

class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Metodo de Pago"
        verbose_name_plural = "Metodos de Pago"

class Pago(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagos')
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia_pago = models.CharField(max_length=100, blank=True, null=True)
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    
    def __str__(self):
        return f"Pago de {self.monto} por {self.reserva}"
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']