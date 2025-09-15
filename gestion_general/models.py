from django.db import models
from django.contrib.auth.models import AbstractUser


# ---------------- Usuario ----------------
class Usuario(AbstractUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('emp', 'Empleado'),
    ]
    rol = models.CharField(max_length=10, choices=ROLES, default='emp')

    def str(self):
        return f"{self.username} ({self.get_rol_display()})"


# ---------------- Producto ----------------
class Producto(models.Model):
    sku = models.CharField(max_length=50, unique=True)  # NRO del producto
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=50, blank=True)
    talla = models.CharField(max_length=50, blank=True)
    unidad = models.CharField(max_length=20, default='unidad')
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def str(self):
        return f"{self.sku} — {self.nombre}"

    def es_critico(self):
        return self.stock_actual <= self.stock_minimo


# ---------------- Pedido ----------------
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

    def str(self):
        return f"Pedido {self.id} - {self.cliente} ({self.estado})"


# ---------------- PedidoInsumo ----------------
class PedidoInsumo(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='insumos'
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def str(self):
        return f"{self.cantidad} x {self.producto.sku}"