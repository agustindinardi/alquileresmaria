from django.db import models

class TipoVehiculo(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Vehiculo"
        verbose_name_plural = "Tipos de Vehiculos"

class Marca(models.Model):
    nombre = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

class Vehiculo(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoVehiculo, on_delete=models.CASCADE)
    ano = models.PositiveIntegerField()
    patente = models.CharField(max_length=10, unique=True)
    capacidad = models.PositiveIntegerField(help_text="Numero de pasajeros")
    tarifa_diaria = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='vehiculos/', blank=True, null=True)
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano}) - {self.patente}"
    
    class Meta:
        verbose_name = "Vehiculo"
        verbose_name_plural = "Vehiculos"
        ordering = ['-ano', 'marca', 'modelo']