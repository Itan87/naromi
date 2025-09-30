from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .models import Usuario, Producto, Pedido, PedidoInsumo


class NaromiAdminSite(admin.AdminSite):
    site_header = 'Naromi Studio'
    site_title = 'Naromi Studio'
    index_title = 'Dashboard'

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Only show Usuario model to admin users
        if request.user.rol != 'admin':
            for app in app_list:
                app['models'] = [
                    model for model in app['models']
                    if model['object_name'] != 'Usuario'
                ]
        return app_list

    def index(self, request, extra_context=None):
        # Get critical stock products
        critical_stock_products = Producto.objects.filter(
            stock_actual__lte=F('stock_minimo')
        ).order_by('stock_actual')[:5]

        # Get active orders
        active_orders = Pedido.objects.exclude(
            estado__in=['completado', 'cancelado']
        )

        # Get recent orders
        recent_orders = Pedido.objects.order_by('-fecha')[:5]

        # Calculate monthly revenue
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = Pedido.objects.filter(
            estado='completado',
            fecha__gte=current_month
        ).aggregate(total=Sum('total'))['total'] or 0

        context = {
            'critical_stock_products': critical_stock_products,
            'critical_stock_count': critical_stock_products.count(),
            'active_orders_count': active_orders.count(),
            'total_products': Producto.objects.count(),
            'monthly_revenue': monthly_revenue,
            'recent_orders': recent_orders,
            **(extra_context or {})
        }
        return super().index(request, context)


# Create custom admin site instance
admin_site = NaromiAdminSite(name='admin')


@admin.register(Usuario, site=admin_site)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol', {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')


@admin.register(Producto, site=admin_site)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'color', 'talla', 'stock_actual', 'stock_minimo', 'estado_stock')
    search_fields = ('sku', 'nombre', 'color')
    list_filter = ('color', 'talla')

    def estado_stock(self, obj):
        if obj.stock_actual <= obj.stock_minimo * 0.5:
            return 'Crítico'
        elif obj.stock_actual <= obj.stock_minimo:
            return 'Bajo'
        return 'Normal'
    estado_stock.short_description = 'Estado'


class PedidoInsumoInline(admin.TabularInline):
    model = PedidoInsumo
    extra = 1


@admin.register(Pedido, site=admin_site)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [PedidoInsumoInline]
    list_display = ('id', 'cliente', 'estado', 'fecha', 'total')
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