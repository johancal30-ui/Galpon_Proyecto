from django.db import models
from django.core.exceptions import ValidationError
from .models import RegistroConsumoForm

class RegistroConsumo(models.Model):
    fecha = models.DateField(auto_now_add=True)
    poblacion_gallinas = models.PositiveIntegerField(default=1000)
    bultos_consumidos = models.DecimalField(max_digits=5, decimal_places=2)
    kilos_por_bulto = models.DecimalField(max_digits=5, decimal_places=2, default=40.0) # Peso por bulto en kg
    stock_disponible = models.DecimalField(max_digits=6, decimal_places=2, default=50.0) # Bultos en stock
    
    # Rango estándar diario de gramos por ave (ejemplo: 100g a 120g)
    CONSUMO_MIN_G_AVE = 80.0
    CONSUMO_MAX_G_AVE = 130.0

    @property
    def consumo_gramos_por_ave(self):
        """Calcula el consumo diario en gramos por ave (g/ave/día)"""
        if self.poblacion_gallinas > 0 and self.bultos_consumidos:
            total_kilos = float(self.bultos_consumidos) * float(self.kilos_por_bulto)
            total_gramos = total_kilos * 1000
            return round(total_gramos / self.poblacion_gallinas, 2)
        return 0.0

    @property
    def es_consumo_anomalo(self):
        """Criterio 2: Verifica si el consumo está fuera del rango esperado"""
        g_ave = self.consumo_gramos_por_ave
        return g_ave < self.CONSUMO_MIN_G_AVE or g_ave > self.CONSUMO_MAX_G_AVE

    def clean(self):
        """Criterio 3: Validaciones de datos"""
        if self.bultos_consumidos is None or self.bultos_consumidos <= 0:
            raise ValidationError({'bultos_consumidos': 'El número de bultos debe ser mayor a cero.'})
        
        if self.bultos_consumidos > self.stock_disponible:
            raise ValidationError({
                'bultos_consumidos': f'La cantidad supera el stock disponible ({self.stock_disponible} bultos).'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)