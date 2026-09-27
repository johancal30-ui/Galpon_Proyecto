from django.urls import path
from . import views

urlpatterns = [
    # Consumo (Jhon)
    path('consumo/', views.registrar_consumo, name='registrar_consumo'),

    # Producción (Johan)
    path('produccion/', views.registrar_produccion, name='registrar_produccion'),
    #path('produccion/editar/<int:pk>/', views.editar_produccion, name='editar_produccion'),
    #path('produccion/eliminar/<int:pk>/', views.eliminar_produccion, name='eliminar_produccion'),

    # Mortalidad (Jeffry)
    path('mortalidad/', views.mortalidad_lista, name='mortalidad_lista'),
    path('mortalidad/registrar/', views.mortalidad_registrar, name='mortalidad_registrar'),
    path('mortalidad/eliminar/<int:pk>/', views.mortalidad_eliminar, name='mortalidad_eliminar'),
    
     # Ventas (Andrés)
    path('ventas/', views.registrar_venta, name='registrar_venta'),
    path('ventas/editar/<int:pk>/', views.editar_venta, name='editar_venta'),
    path('ventas/eliminar/<int:pk>/', views.eliminar_venta, name='eliminar_venta'),
]