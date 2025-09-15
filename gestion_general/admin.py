from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Producto, Pedido, PedidoInsumo


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol', {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'color', 'talla', 'stock_actual', 'stock_minimo')
    search_fields = ('sku', 'nombre', 'color')
    list_filter = ('color', 'talla')


class PedidoInsumoInline(admin.TabularInline):
    model = PedidoInsumo
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [PedidoInsumoInline]
    list_display = ('id', 'cliente', 'estado', 'fecha')
    list_filter = ('estado', 'fecha')

    def save_model(self, request, obj, form, change):
        es_admin = request.user.rol == 'admin'
        if not es_admin and obj.estado == 'orden_trabajo':
            alertas = []
            for pedido_insumo in obj.insumos.all():
                if pedido_insumo.cantidad > pedido_insumo.producto.stock_actual:
                    alertas.append(
                        f"{pedido_insumo.producto.nombre}: {pedido_insumo.cantidad} "
                        f"(Stock actual: {pedido_insumo.producto.stock_actual})"
                    )
            if alertas:
                mensaje = "Stock insuficiente para los siguientes insumos:\n" + "\n".join(alertas)
                self.message_user(request, mensaje, level=messages.WARNING)
                obj.estado = 'presupuestado'
        super().save_model(request, obj, form, change)