from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('recuperar-contrasena/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('validar-codigo/', views.validar_codigo, name='validar_codigo'),
    
    # URLs para empleados (solo administradores)
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleados/confirmar-baja/', views.confirmar_baja_empleado, name='confirmar_baja_empleado'),
    path('empleados/<int:empleado_id>/eliminar/', views.eliminar_empleado, name='eliminar_empleado'),
]