# script_datos_iniciales.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alquileres_maria.settings')
django.setup()

from django.contrib.auth.models import User
from vehiculos.models import TipoVehiculo, Marca, Vehiculo
from reservas.models import EstadoReserva
from pagos.models import MetodoPago
from decimal import Decimal

#!/usr/bin/env python
import os
import sys

# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alquileres_maria.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)

# if __name__ == '__main__':
#     main()


#Crear estados de reserva
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

#Crear algunos vehiculos de ejemplo
vehiculos = [
    {
        'marca': 'Toyota',
        'modelo': 'Corolla',
        'tipo': 'Sedan',
        'ano': 2022,
        'patente': 'ABC123',
        'capacidad': 5,
        'tarifa_diaria': Decimal('50.00'),
        'descripcion': 'Toyota Corolla en excelente estado. Ideal para viajes familiares.'
    },
    {
        'marca': 'Ford',
        'modelo': 'EcoSport',
        'tipo': 'SUV',
        'ano': 2021,
        'patente': 'DEF456',
        'capacidad': 5,
        'tarifa_diaria': Decimal('60.00'),
        'descripcion': 'Ford EcoSport con todas las comodidades. Perfecta para ciudad y ruta.'
    },
    {
        'marca': 'Chevrolet',
        'modelo': 'S10',
        'tipo': 'Camioneta',
        'ano': 2020,
        'patente': 'GHI789',
        'capacidad': 5,
        'tarifa_diaria': Decimal('70.00'),
        'descripcion': 'Chevrolet S10 4x4. Ideal para terrenos dificiles y carga.'
    }
]

for v in vehiculos:
    marca = Marca.objects.get(nombre=v['marca'])
    tipo = TipoVehiculo.objects.get(nombre=v['tipo'])
    
    Vehiculo.objects.get_or_create(
        patente=v['patente'],
        defaults={
            'marca': marca,
            'modelo': v['modelo'],
            'tipo': tipo,
            'ano': v['ano'],
            'capacidad': v['capacidad'],
            'tarifa_diaria': v['tarifa_diaria'],
            'descripcion': v['descripcion'],
            'disponible': True
        }
    )
print("Vehiculos de ejemplo creados")

print("Datos iniciales creados exitosamente")

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