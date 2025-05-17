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

class PoliticaReembolso(models.Model):
    nombre = models.CharField(max_length=50)  # Ejemplo: "100%", "20%", "Sin reembolso"
    porcentaje = models.PositiveIntegerField(help_text="Porcentaje de reembolso (0-100)")
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Política de Reembolso'
        verbose_name_plural = 'Políticas de Reembolso'
    
    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

class Vehiculo(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoVehiculo, on_delete=models.CASCADE)
    ano = models.PositiveIntegerField()
    patente = models.CharField(max_length=10, unique=True)
    capacidad = models.PositiveIntegerField(help_text="Numero de pasajeros")
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2)
    kilometraje = models.PositiveIntegerField(help_text='Kilometraje actual del vehículo', default=0)
    descripcion = models.TextField(blank=True, null=True)
    politica_reembolso = models.ForeignKey(PoliticaReembolso, on_delete=models.SET_NULL, null=True, blank=True)
    imagen = models.ImageField(upload_to='vehiculos/', blank=True, null=True)
    disponible = models.BooleanField(default=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano}) - {self.patente}"

    class Meta:
        verbose_name = "Vehiculo"
        verbose_name_plural = "Vehiculos"
        ordering = ['-ano', 'marca', 'modelo']