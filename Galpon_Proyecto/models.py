from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

# REGISTRO DE PRODUCCIÓN (JOHAN)

class RegistroProduccion(models.Model):
    fecha = models.DateField(default=timezone.now)
    cantidad_huevos = models.PositiveIntegerField()
    cantidad_cubetas = models.PositiveIntegerField()
    cantidad_huevos_rotos = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Registro {self.fecha} - {self.cantidad_huevos} huevos / {self.cantidad_cubetas} cubetas"



# REGISTRO DE CONSUMO DE ALIMENTO (JHON)
class RegistroConsumo(models.Model):
    fecha = models.DateField(default=timezone.now)
    poblacion_gallinas = models.PositiveIntegerField(default=1000)
    bultos_consumidos = models.DecimalField(max_digits=5, decimal_places=2)
    kilos_por_bulto = models.DecimalField(max_digits=5, decimal_places=2, default=40.0)
    stock_disponible = models.DecimalField(max_digits=6, decimal_places=2, default=50.0)

    # Rango estándar diario de gramos por ave
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
        """Verifica si el consumo está fuera del rango esperado"""
        g_ave = self.consumo_gramos_por_ave
        return g_ave < self.CONSUMO_MIN_G_AVE or g_ave > self.CONSUMO_MAX_G_AVE

    def clean(self):
        """Validaciones de datos"""
        if self.bultos_consumidos is None or self.bultos_consumidos <= 0:
            raise ValidationError({'bultos_consumidos': 'El número de bultos debe ser mayor a cero.'})

        if self.bultos_consumidos > self.stock_disponible:
            raise ValidationError({
                'bultos_consumidos': f'La cantidad supera el stock disponible ({self.stock_disponible} bultos).'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

#(JEFFRY)

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

# REGISTRO DE MORTALIDAD (JEFFRY)
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


# VENTA DE HUEVOS Y CUBETAS (ANDRÉS)
class Venta(models.Model):
    fecha = models.DateField(default=timezone.now)
    cliente = models.CharField(max_length=150)
    cantidad_huevos = models.PositiveIntegerField()
    cantidad_cubetas = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio por cubeta")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha} - {self.cliente} - ${self.total}"

    def save(self, *args, **kwargs):
        # Calcular el total automáticamente antes de guardar
        self.total = self.cantidad_cubetas * self.precio_unitario
        super().save(*args, **kwargs)


# INVENTARIO DE ALIMENTO (ANDRÉS)

class Alimento(models.Model):
    TIPOS = [
        ('iniciador', 'Iniciador'),
        ('engorde', 'Engorde'),
        ('finalizador', 'Finalizador'),
        ('medicado', 'Medicado'),
    ]

    fecha = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cantidad_bultos = models.PositiveIntegerField()
    kilos_por_bulto = models.DecimalField(max_digits=5, decimal_places=2, default=40.0)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    proveedor = models.CharField(max_length=150)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha} - {self.get_tipo_display()} - {self.cantidad_bultos} bultos"

    def save(self, *args, **kwargs):
        # Calcular costo total automáticamente
        self.costo_total = self.cantidad_bultos * self.costo_unitario
        super().save(*args, **kwargs)