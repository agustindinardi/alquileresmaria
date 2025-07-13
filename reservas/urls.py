from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.ReservaListView.as_view(), name='lista'),
    path('<int:pk>/', views.ReservaDetailView.as_view(), name='detalle'),
    path('crear/<int:vehiculo_id>/', views.crear_reserva, name='crear'),
    path('cancelar/<int:pk>/', views.cancelar_reserva, name='cancelar'),
    path('admin-cancelar/<int:pk>/', views.admin_cancelar_reserva, name='admin_cancelar'),
    path('crearReserva_empleado/<int:vehiculo_id>/', views.crear_reserva_Emple, name='crearReserva_empleado'),

    path('sucursal/', views.ReservaSucursalListView.as_view(), name='reservas_sucursal'),
    path('entrega/<int:reserva_id>/', views.registrar_entrega, name='registrar_entrega'),
    path('devolucion/<int:reserva_id>/', views.registrar_devolucion_simple, name='registrar_devolucion_simple'),
    path('devolucion-mantenimiento/<int:reserva_id>/', views.registrar_devolucion_mantenimiento, name='registrar_devolucion_mantenimiento'),
]