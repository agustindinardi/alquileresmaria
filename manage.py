# manage.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alquileres_maria.settings')
django.setup()

from django.contrib.auth.models import User
from vehiculos.models import PoliticaReembolso, TipoVehiculo, Marca, Vehiculo, Sucursal
from reservas.models import EstadoReserva
from pagos.models import MetodoPago
from decimal import Decimal

#!/usr/bin/env python
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alquileres_maria.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
    
# Crear políticas de reembolso
politicas_reembolso = [
    {'nombre': 'Reembolso Completo', 'porcentaje': 100, 'descripcion': 'Devolución del 100% del importe pagado.'},
    {'nombre': 'Reembolso Parcial', 'porcentaje': 20, 'descripcion': 'Devolución del 20% del importe pagado.'},
    {'nombre': 'Sin Reembolso', 'porcentaje': 0, 'descripcion': 'No se realiza ningún reembolso.'}
]

for politica in politicas_reembolso:
    PoliticaReembolso.objects.get_or_create(
        nombre=politica['nombre'],
        defaults={
            'porcentaje': politica['porcentaje'],
            'descripcion': politica['descripcion']
        }
    )
print("Políticas de reembolso creadas")

# Crear sucursales
sucursales_data = [
    {'nombre': 'Sucursal Central', 'direccion': 'Av. 7 1234', 'ciudad': 'La Plata'},
    {'nombre': 'Sucursal Norte', 'direccion': 'Calle 60 456', 'ciudad': 'La Plata'},
    {'nombre': 'Sucursal Sur', 'direccion': 'Calle 137 789', 'ciudad': 'Berisso'}
]

for data in sucursales_data:
    Sucursal.objects.get_or_create(
        nombre=data['nombre'],
        defaults={
            'direccion': data['direccion'],
            'ciudad': data['ciudad']
        }
    )
print("Sucursales creadas")

# Crear estados de reserva
estados_reserva = ['Pendiente', 'Confirmada', 'Cancelada', 'Cancelada por Admin', 'Completada']
for estado in estados_reserva:
    EstadoReserva.objects.get_or_create(nombre=estado)
print("Estados de reserva creados")

# Crear metodos de pago
metodos_pago = ['Tarjeta de Credito/Debito', 'Transferencia Bancaria', 'Efectivo']
for metodo in metodos_pago:
    MetodoPago.objects.get_or_create(nombre=metodo)
print("Metodos de pago creados")

# Crear tipos de vehiculos
tipos_vehiculo = ['Sedan', 'SUV', 'Camioneta', 'Compacto', 'Deportivo', 'Minivan']
for tipo in tipos_vehiculo:
    TipoVehiculo.objects.get_or_create(nombre=tipo)
print("Tipos de vehiculo creados")

# Crear marcas
marcas = ['Toyota', 'Ford', 'Chevrolet', 'Volkswagen', 'Honda', 'Nissan', 'Renault', 'Fiat']
for marca in marcas:
    Marca.objects.get_or_create(nombre=marca)
print("Marcas creadas")

# Crear superusuario si no existe
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    user.last_login = user.date_joined  # Asignamos la fecha de creación como last_login
    user.save()
    print("Superusuario creado")

# Crear algunos vehiculos de ejemplo
vehiculos = [
    {
        'marca': 'Toyota',
        'modelo': 'Corolla',
        'tipo': 'Sedan',
        'ano': 2022,
        'patente': 'ABC123',
        'capacidad': 5,
        'precio_por_dia': Decimal('50.00'),  # Actualizado nombre del campo
        'kilometraje': 15000,  # Añadido nuevo campo
        'politica_reembolso': 'Reembolso Completo',  # Añadido nuevo campo
        'descripcion': 'Toyota Corolla en excelente estado. Ideal para viajes familiares.',
        'sucursal': 'La Plata'
    },
    {
        'marca': 'Ford',
        'modelo': 'EcoSport',
        'tipo': 'SUV',
        'ano': 2021,
        'patente': 'DEF456',
        'capacidad': 5,
        'precio_por_dia': Decimal('60.00'),  # Actualizado nombre del campo
        'kilometraje': 25000,  # Añadido nuevo campo
        'politica_reembolso': 'Reembolso Parcial',  # Añadido nuevo campo
        'descripcion': 'Ford EcoSport con todas las comodidades. Perfecta para ciudad y ruta.',
        'sucursal': 'La Plata'
    },
    {
        'marca': 'Chevrolet',
        'modelo': 'S10',
        'tipo': 'Camioneta',
        'ano': 2020,
        'patente': 'GHI789',
        'capacidad': 5,
        'precio_por_dia': Decimal('70.00'),  # Actualizado nombre del campo
        'kilometraje': 35000,  # Añadido nuevo campo
        'politica_reembolso': 'Sin Reembolso',  # Añadido nuevo campo
        'descripcion': 'Chevrolet S10 4x4. Ideal para terrenos dificiles y carga.',
        'sucursal': 'La Plata'
    }
]


for v in vehiculos:
    marca = Marca.objects.get(nombre=v['marca'])
    tipo = TipoVehiculo.objects.get(nombre=v['tipo'])
    politica = PoliticaReembolso.objects.get(nombre=v['politica_reembolso'])
    sucursal = Sucursal.objects.get(nombre='Sucursal Central')  # Usada para todos los vehículos
    
    Vehiculo.objects.get_or_create(
        patente=v['patente'],
        defaults={
            'marca': marca,
            'modelo': v['modelo'],
            'tipo': tipo,
            'ano': v['ano'],
            'capacidad': v['capacidad'],
            'precio_por_dia': v['precio_por_dia'],
            'kilometraje': v['kilometraje'],
            'politica_reembolso': politica,
            'descripcion': v['descripcion'],
            'disponible': True,
            'sucursal': sucursal  # Aquí se asigna la sucursal
        }
    )
print("Vehiculos de ejemplo creados")

print("Datos iniciales creados exitosamente")