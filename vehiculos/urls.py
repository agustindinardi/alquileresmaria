from django.urls import path
from . import views

app_name = 'vehiculos'

urlpatterns = [
    path('', views.VehiculoListView.as_view(), name='lista'),
    path('<int:pk>/', views.VehiculoDetailView.as_view(), name='detalle'),
]