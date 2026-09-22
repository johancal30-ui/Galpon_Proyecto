from django.urls import path
from . import views

urlpatterns = [
    # Ruta de Consumo (rama Gato)
    path('consumo/', views.registrar_consumo, name='registrar_consumo'),
    
    # Rutas de Producción (tu Historia de Usuario)
    path('produccion/', views.registrar_produccion, name='registrar_produccion'),
    path('produccion/editar/<int:pk>/', views.editar_produccion, name='editar_produccion'),
    path('produccion/eliminar/<int:pk>/', views.eliminar_produccion, name='eliminar_produccion'),
]