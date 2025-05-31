# manage.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alquileres_maria.settings')
django.setup()

from django.contrib.auth.models import User
from vehiculos.models import Estado, PoliticaReembolso, TipoVehiculo, Marca, Vehiculo, Sucursal
from reservas.models import EstadoReserva
from pagos.models import MetodoPago
from reservas.models import Tarjeta
from decimal import Decimal
from usuarios.models import Perfil  # Asegurate de que esté importado
from datetime import date

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

# Crear estados de vehículos
estados_vehiculos = [
    {'nombre': 'Disponible'},
    {'nombre': 'Reservado'},
    {'nombre': 'Mantenimiento'},
]

for estado in estados_vehiculos:
    Estado.objects.get_or_create(
        nombre=estado['nombre']
    )
print("Estados de vehículos creados")

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
estados_reserva = ['Cancelada', 'Confirmada', 'Cancelada', 'Cancelada por Admin', 'Completada']
for estado in estados_reserva:
    EstadoReserva.objects.get_or_create(nombre=estado)
print("Estados de reserva creados")



# Crear metodos de pago
metodos_pago = ['Tarjeta de Credito/Debito', 'Efectivo']
for metodo in metodos_pago:
    MetodoPago.objects.get_or_create(nombre=metodo)
print("Metodos de pago creados")

# Crear tipos de vehiculos
tipos_vehiculo = ['Sedan', 'SUV', 'Camioneta', 'Compacto', 'Deportivo', 'Minivan']
for tipo in tipos_vehiculo:
    TipoVehiculo.objects.get_or_create(nombre=tipo)
print("Tipos de vehiculo creados")

# Crear superusuario si no existe
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'alquileresmaria4@gmail.com', 'admin123')
    user.last_login = user.date_joined  # Asignamos la fecha de creación como last_login
    user.save()
    print("Superusuario creado")

usuarios_data = [
    {
        'first_name': 'Juan',
        'last_name': 'Perez',
        'email': 'juan@gmail.com',
        'dni': '111111111',
        'telefono': '2211234567',
        'fecha_nacimiento': date(1995, 12, 12),
        'password': 'juan'
    },
    {
        'first_name': 'Pepe',
        'last_name': 'Juarez',
        'email': 'pepe@gmail.com',
        'dni': '222222222',
        'telefono': '2217654321',
        'fecha_nacimiento': date(1995, 12, 12),
        'password': 'pepe'
    }
]

for u in usuarios_data:
    if not User.objects.filter(username=u['email']).exists():
        user = User.objects.create_user(
            username=u['email'],
            email=u['email'],
            password=u['password'],
            first_name=u['first_name'],
            last_name=u['last_name']
        )
        Perfil.objects.create(
            usuario=user,
            dni=u['dni'],
            telefono=u['telefono'],
            fecha_nacimiento=u['fecha_nacimiento']
        )
        print(f"Usuario creado: {u['first_name']} {u['last_name']} ({u['email']})")
    else:
        print(f"Usuario ya existe: {u['email']}")

# Crear algunos vehículos de ejemplo
vehiculos = [
    {
        'marca': 'Toyota',
        'modelo': 'Corolla',
        'tipo': 'Sedan',
        'ano': 2022,
        'patente': 'ABC123',
        'capacidad': 5,
        'precio_por_dia': Decimal('50.00'),
        'kilometraje': 15000,
        'politica_reembolso': 'Reembolso Completo',
        'descripcion': 'Toyota Corolla en excelente estado. Ideal para viajes familiares.',
        'sucursal': 'Sucursal Central',
        'estado': 'Disponible'
    },
    {
        'marca': 'Ford',
        'modelo': 'EcoSport',
        'tipo': 'SUV',
        'ano': 2021,
        'patente': 'DEF456',
        'capacidad': 5,
        'precio_por_dia': Decimal('60.00'),
        'kilometraje': 25000,
        'politica_reembolso': 'Reembolso Parcial',
        'descripcion': 'Ford EcoSport con todas las comodidades. Perfecta para ciudad y ruta.',
        'sucursal': 'Sucursal Norte',
        'estado': 'Disponible'
    },
    {
        'marca': 'Chevrolet',
        'modelo': 'S10',
        'tipo': 'Camioneta',
        'ano': 2020,
        'patente': 'GHI789',
        'capacidad': 5,
        'precio_por_dia': Decimal('70.00'),
        'kilometraje': 35000,
        'politica_reembolso': 'Sin Reembolso',
        'descripcion': 'Chevrolet S10 4x4. Ideal para terrenos difíciles y carga.',
        'sucursal': 'Sucursal Central',
        'estado': 'Reservado'
    }
]

vehiculos_creados = 0
for v in vehiculos:
    try:
        tipo = TipoVehiculo.objects.get(nombre=v['tipo'])
        politica = PoliticaReembolso.objects.get(nombre=v['politica_reembolso'])
        sucursal = Sucursal.objects.get(nombre=v['sucursal'])
        estado = Estado.objects.get(nombre=v['estado'])  # Instancia de Estado

        vehiculo, created = Vehiculo.objects.get_or_create(
            patente=v['patente'],
            defaults={
                'marca': v['marca'],
                'modelo': v['modelo'],
                'tipo': tipo,
                'ano': v['ano'],
                'capacidad': v['capacidad'],
                'precio_por_dia': v['precio_por_dia'],
                'kilometraje': v['kilometraje'],
                'politica_reembolso': politica,
                'descripcion': v['descripcion'],
                'estado': estado,  # Asignar la instancia de Estado
                'sucursal': sucursal
            }
        )

        if created:
            vehiculos_creados += 1
            print(f"  → {vehiculo} - {estado}")

    except Exception as e:
        print(f"✗ Error creando vehículo {v['patente']}: {e}")

print(f"✓ {vehiculos_creados} vehículos de ejemplo creados")

# Mostrar resumen de estados
print("\n📊 Resumen de vehículos por estado:")
for estado in Estado.objects.all():
    count = Vehiculo.objects.filter(estado=estado).count()
    if count > 0:
        print(f"  → {estado.nombre}: {count} vehículo(s)")

print("Vehículos de ejemplo creados")

# Plantillas de tarjetas de crédito
tarjetas_template = [
    {
        'tipo': 'credito', # Tarjeta de credito con saldo suficiente y vencimiento valido 
        'numero': '1234567890101112',
        'vencimiento': '2032-12-31',  
        'pin': '112',  
        'saldo': Decimal('2000.00'),
        'dni_titular': '111111111' # DNI del titular Juan  
    },
    {
        'tipo': 'debito', # Tarjeta de debito con saldo mas o menos y vencimiento valido
        'numero': '1211100987654321',
        'vencimiento': '2031-01-01',
        'pin': '321',
        'saldo': Decimal('500.00'),
        'dni_titular': '222222222' # DNI del titular Pepe
    },
    {
        'tipo': 'credito',  # Tarjeta de credito vencida
        'numero': '1314151617181920',
        'vencimiento': '2023-12-12',
        'pin': '920',
        'saldo': Decimal('0.00'),
        'dni_titular': '000000000'
    }
]

for tarjeta_data in tarjetas_template:
    Tarjeta.objects.get_or_create(
        numero=tarjeta_data['numero'],
        defaults={
            'tipo': tarjeta_data['tipo'],
            'vencimiento': tarjeta_data['vencimiento'],
            'pin': tarjeta_data['pin'],
            'saldo': tarjeta_data['saldo'],
            'dni_titular': tarjeta_data['dni_titular']
        }
    )

print("Tarjetas de ejemplo creadas")

print("Datos iniciales creados exitosamente")
