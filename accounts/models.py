from django.db import models
from django.contrib.auth.models import User


class Lote(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_ingreso = models.DateField()
    cantidad_inicial = models.PositiveIntegerField(help_text="Cantidad de gallinas al iniciar el lote")

    def __str__(self):
        return self.nombre

    @property
    def total_muertes(self):
        return self.mortalidades.aggregate(total=models.Sum('cantidad'))['total'] or 0

    @property
    def aves_vivas(self):
        return self.cantidad_inicial - self.total_muertes


class RegistroMortalidad(models.Model):
    CAUSAS = [
        ('enfermedad', 'Enfermedad'),
        ('calor', 'Estrés calórico'),
        ('depredador', 'Depredador'),
        ('accidente', 'Accidente'),
        ('desconocida', 'Causa desconocida'),
        ('otra', 'Otra'),
    ]

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='mortalidades')
    fecha = models.DateField()
    cantidad = models.PositiveIntegerField()
    causa = models.CharField(max_length=20, choices=CAUSAS, default='desconocida')
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.lote} - {self.fecha} ({self.cantidad})"