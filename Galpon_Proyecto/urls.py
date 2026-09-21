from django.urls import path
from . import views

urlpatterns = [
    path('consumo/', views.registrar_consumo, name='registrar_consumo'),
]