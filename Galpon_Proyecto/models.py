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

# Rango estándar diario de gramos por gallina
    CONSUMO_MIN_G_AVE = 80.0
    CONSUMO_MAX_G_AVE = 130.0

    @property
    def consumo_gramos_por_ave(self):
        """Calcula el consumo diario en gramos por gallina (g/ave/día)"""
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
# INVENTARIO Y ALERTAS DE STOCK (JHON)

class Inventario(models.Model):
    TIPOS_INSUMO = [
        ('alimento', 'Alimento'),
        ('vacuna', 'Vacuna'),
    ]

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_INSUMO
    )

    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'

    def __str__(self):
        return f"{self.get_tipo_display()} - Stock: {self.stock_actual}"

    @property
    def stock_bajo(self):
        """
        Determina si el stock está en el límite mínimo
        o por debajo de este.
        """
        return self.stock_actual <= self.stock_minimo

    def verificar_alerta(self):
        """
        Crea una alerta cuando el stock está en el mínimo
        o por debajo de este.

        Si el stock vuelve a estar por encima del mínimo,
        resuelve automáticamente las alertas activas.
        """

        if self.stock_bajo:
            AlertaStock.objects.get_or_create(
                inventario=self,
                activa=True,
                defaults={
                    'mensaje': (
                        f'El stock de {self.get_tipo_display()} '
                        f'está bajo. Stock actual: {self.stock_actual}. '
                        f'Mínimo permitido: {self.stock_minimo}.'
                    )
                }
            )

        else:
            alertas_activas = self.alertas.filter(activa=True)

            alertas_activas.update(
                activa=False,
                resuelta_en=timezone.now()
            )
    
class AlertaStock(models.Model):
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name='alertas'
    )

    mensaje = models.CharField(max_length=255)

    activa = models.BooleanField(default=True)

    creada_en = models.DateTimeField(auto_now_add=True)
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = 'Alerta de stock'
        verbose_name_plural = 'Alertas de stock'

    def __str__(self):
        estado = 'Activa' if self.activa else 'Resuelta'
        return f"{self.inventario.get_tipo_display()} - {estado}"

# GASTOS OPERATIVOS ANDRES
class GastoOperativo(models.Model):
    CATEGORIAS = [
        ('servicios', 'Servicios públicos'),
        ('transporte', 'Transporte'),
        ('empaque', 'Empaque'),
        ('mano_obra', 'Mano de obra'),
        ('insumos', 'Insumos'),
        ('otro', 'Otro'),
    ]

    fecha = models.DateField(auto_now_add=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    descripcion = models.CharField(max_length=200, help_text="Detalle del gasto")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Gasto operativo'
        verbose_name_plural = 'Gastos operativos'

    def __str__(self):
        return f"{self.fecha} - {self.get_categoria_display()} - ${self.monto}"