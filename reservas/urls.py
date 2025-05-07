from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.ReservaListView.as_view(), name='lista'),
    path('<int:pk>/', views.ReservaDetailView.as_view(), name='detalle'),
    path('crear/<int:vehiculo_id>/', views.crear_reserva, name='crear'),
    path('cancelar/<int:pk>/', views.cancelar_reserva, name='cancelar'),
    path('admin-cancelar/<int:pk>/', views.admin_cancelar_reserva, name='admin_cancelar'),
]