from django.db import models

class RegistroProduccion(models.Model):
    fecha = models.DateField(auto_now_add=True)  # Guarda la fecha automáticamente
    huevos_recolectados = models.IntegerField()
    cubetas_armadas = models.IntegerField()

    def __str__(self):
        return f"{self.fecha} - {self.huevos_recolectados} huevos"