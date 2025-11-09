from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum, Count
from django.utils import timezone


class Usuario(AbstractUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('emp', 'Empleado'),
    ]
    rol = models.CharField(max_length=10, choices=ROLES, default='emp')

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField(max_length=254, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    # NUEVO CAMPO BOOLEANO
    #tiene_email = models.BooleanField(
     #   default=False, 
      #  editable=False, 
       # verbose_name='Email Registrado'
    #)
    @property
    def tiene_email(self):
        return bool(self.email and self.email.strip())    

    def __str__(self):
        return f"{self.nombre} ({self.email})"

    def save(self, *args, **kwargs):
        # La lógica se ejecuta ANTES de guardar el cliente.
        # Limpiar espacios invisibles del email si existe
        if self.email:
            self.email = self.email.strip()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Insumo(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    unidad = models.CharField(max_length=20, default='unidad')
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.sku} — {self.nombre}"

    def es_critico(self):
        return self.stock_actual <= self.stock_minimo

    def estado_stock(self):
        if self.stock_actual <= self.stock_minimo * 0.5:
            return 'critico'
        elif self.stock_actual <= self.stock_minimo:
            return 'bajo'
        return 'normal'

    @classmethod
    def obtener_insumos_criticos(cls):
        return cls.objects.filter(stock_actual__lte=models.F('stock_minimo'))

    @classmethod
    def obtener_metricas_stock(cls):
        total = cls.objects.count()
        criticos = cls.objects.filter(stock_actual__lte=models.F('stock_minimo')).count()
        return {
            'total': total,
            'criticos': criticos,
            'porcentaje_critico': (criticos / total * 100) if total > 0 else 0
        }


class Pedido(models.Model):
    ESTADOS = [
        ('ingresado', 'Ingresado'),
        ('presupuestado', 'Presupuestado'),
        ('aprobado', 'Aprobado'),
        ('orden_trabajo', 'Orden de Trabajo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ingresado')
    creado_por = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_creados'
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    descuento = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Monto Descuento',
        blank=True
    )
    total_final = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Total Final',
        blank=True
    )

    def save(self, *args, **kwargs):
        MONTO_MINIMO = Decimal('500000.00')
        PORCENTAJE_DESCUENTO = Decimal('0.10')

          # Si no hay cliente aún, guardamos sin descuento
        if not self.cliente_id:
            super().save(*args, **kwargs)
            return

    # Refrescamos cliente desde BD
        cliente = Cliente.objects.get(pk=self.cliente_id)
        tiene_email = cliente.tiene_email

    # Calcular descuento
        if self.total and self.total >= MONTO_MINIMO and tiene_email:
            self.descuento = self.total * PORCENTAJE_DESCUENTO
            self.total_final = self.total - self.descuento
        else:
            self.descuento = 0
            self.total_final = self.total or 0

        super().save(*args, **kwargs)
           
    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.nombre} ({self.estado})"

    @classmethod
    def obtener_pedidos_activos(cls):
        return cls.objects.exclude(estado__in=['completado', 'cancelado'])

    @classmethod
    def obtener_ingresos_mes(cls):
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return cls.objects.filter(
            estado='completado',
            fecha__gte=inicio_mes
        ).aggregate(total=Sum('total'))['total'] or 0

    @classmethod
    def obtener_metricas_pedidos(cls):
        total = cls.objects.count()
        activos = cls.obtener_pedidos_activos().count()
        completados = cls.objects.filter(estado='completado').count()
        return {
            'total': total,
            'activos': activos,
            'completados': completados,
            'porcentaje_completados': (completados / total * 100) if total > 0 else 0
        }


class PedidoInsumo(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='insumos'
    )
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.insumo.sku}"