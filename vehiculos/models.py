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

class Estado(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

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

    # Nuevo: estado como relación
    estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, blank=True)

    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_cambio_estado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano}) - {self.patente}"

    # Propiedades de estado
    def disponible(self):
        return self.estado and self.estado.nombre.lower() == "disponible"

    def esta_reservado(self):
        return self.estado and self.estado.nombre.lower() == "reservado"

    def en_mantenimiento(self):
        return self.estado and self.estado.nombre.lower() == "mantenimiento"

    # Métodos de cambio de estado
    def cambiar_estado(self, nuevo_estado_nombre, save=True):
        try:
            nuevo_estado = Estado.objects.get(nombre__iexact=nuevo_estado_nombre)
        except Estado.DoesNotExist:
            return False

        self.estado = nuevo_estado
        if save:
            self.save(update_fields=['estado', 'fecha_cambio_estado'])
        return True

    def reservar(self):
        if self.disponible():
            return self.cambiar_estado("disponible")
        return False

    def liberar(self):
        if self.esta_reservado() or self.en_mantenimiento():
            return self.cambiar_estado("disponible")
        return False

    def enviar_a_mantenimiento(self):
        if self.disponible():
            return self.cambiar_estado("mantenimiento")
        return False

    def get_estado_color_class(self):
        color_map = {
            "disponible": 'bg-success',
            "reservado": 'bg-warning',
            "mantenimiento": 'bg-danger',
        }
        return color_map.get(self.estado.nombre.lower(), 'bg-secondary') if self.estado else 'bg-secondary'

    def get_estado_display_with_icon(self):
        icon_map = {
            "disponible": '✅',
            "reservado": '📅',
            "mantenimiento": '🔧',
        }
        if self.estado:
            nombre = self.estado.nombre.capitalize()
            icono = icon_map.get(self.estado.nombre.lower(), '❓')
            return f"{icono} {nombre}"
        return "❓ Sin estado"

    class Meta:
        verbose_name = "Vehiculo"
        verbose_name_plural = "Vehiculos"
        ordering = ['-ano', 'marca', 'modelo']
