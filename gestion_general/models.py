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


class Producto(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=50, blank=True)
    talla = models.CharField(max_length=50, blank=True)
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
    def obtener_productos_criticos(cls):
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
    cliente = models.CharField(max_length=200)
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

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente} ({self.estado})"

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
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.sku}"