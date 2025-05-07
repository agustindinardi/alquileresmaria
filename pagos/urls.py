from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    path('procesar/<int:reserva_id>/', views.procesar_pago, name='procesar_pago'),
    path('historial/', views.historial_pagos, name='historial'),
]