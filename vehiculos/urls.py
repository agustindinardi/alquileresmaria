# from django.urls import path
# from . import views

# app_name = 'vehiculos'

# urlpatterns = [
#     path('', views.VehiculoListView.as_view(), name='lista'),
#     path('<int:pk>/', views.VehiculoDetailView.as_view(), name='detalle'),
# ]

from django.urls import path
from . import views

app_name = 'vehiculos'

urlpatterns = [
    # Listado de vehículos
    path('', views.VehiculoListView.as_view(), name='lista'),

    # Detalles de un vehículo específico
    path('vehiculo/<int:pk>/', views.VehiculoDetailView.as_view(), name='vehiculo-detail'),

    # Crear nuevo vehículo
    path('vehiculo/nuevo/', views.VehiculoCreateView.as_view(), name='vehiculo-create'),

    # Actualizar vehículo existente
    path('vehiculo/<int:pk>/editar/', views.VehiculoUpdateView.as_view(), name='vehiculo-update'),

    # Eliminar vehículo
    path('vehiculo/<int:pk>/eliminar/', views.VehiculoDeleteView.as_view(), name='vehiculo-delete'),
]