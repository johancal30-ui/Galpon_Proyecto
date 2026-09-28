from django.urls import path
from . import views

urlpatterns = [
    path('consumo/', views.registrar_consumo, name='registrar_consumo'),
    path('', views.registrar_produccion, name='registrar_produccion'),
    path('editar/<int:id>/', views.editar_produccion, name='editar_produccion'),
    path('eliminar/<int:id>/', views.eliminar_produccion, name='eliminar_produccion'),
]