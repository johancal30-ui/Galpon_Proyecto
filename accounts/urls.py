from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('cierre/', views.cierre, name='logout'),
    path('', views.home_view, name='home'),
    path('recuperar/', views.password_reset_view.as_view(), name='recuperar'),
    path('recuperar/enviado/', views.password_reset_done_view.as_view(), name='recuperar_enviado'),
    path('recuperar/<uidb64>/<token>/', views.password_reset_confirm_view.as_view(), name='recuperar_confirmar'),
    path('recuperar/completado/', views.password_reset_complete_view.as_view(), name='recuperar_completado'),

    path('mortalidad/', views.mortalidad_lista, name='mortalidad_lista'),
    path('mortalidad/registrar/', views.mortalidad_registrar, name='mortalidad_registrar'),
    path('mortalidad/eliminar/<int:pk>/', views.mortalidad_eliminar, name='mortalidad_eliminar'),
]