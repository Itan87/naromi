from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.html import format_html
from django import forms
from django.shortcuts import redirect
from django.urls import reverse, path
from django.http import HttpResponseRedirect, HttpResponse
import logging
from .models import Usuario, Insumo, Pedido, PedidoInsumo, Cliente

# Set up logging
logger = logging.getLogger(__name__)


class PedidoAdminForm(forms.ModelForm):
    """
    Custom form for Pedido that handles estado changes from Aprobado to Orden de Trabajo
    with stock validation and confirmation.
    """
    
    class Meta:
        model = Pedido
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_estado = None
        if self.instance and self.instance.pk:
            self.original_estado = self.instance.estado
    
    def clean_estado(self):
        """
        Validate estado change from Aprobado to Orden de Trabajo.
        This method will be called during form validation.
        """
        new_estado = self.cleaned_data.get('estado')
        
        # Log the estado change attempt
        logger.info(f"PedidoAdminForm: Attempting estado change from '{self.original_estado}' to '{new_estado}' for Pedido {self.instance.pk}")
        print(f"FORM DEBUG: Estado change from '{self.original_estado}' to '{new_estado}' for Pedido {self.instance.pk}")
        
        # Check if we're changing from Aprobado to Orden de Trabajo
        if (self.original_estado == 'aprobado' and 
            new_estado == 'orden_trabajo'):
            
            logger.info(f"🚨 DETECTED: Estado change from Aprobado to Orden de Trabajo for Pedido {self.instance.pk}")
            print(f"🚨 DETECTED: Estado change from Aprobado to Orden de Trabajo for Pedido {self.instance.pk}")
            
            # Validate stock availability
            insufficient_items = []
            for pedido_insumo in self.instance.insumos.all():
                if pedido_insumo.cantidad > pedido_insumo.insumo.stock_actual:
                    insufficient_items.append(
                        f"{pedido_insumo.insumo.nombre}: necesita {pedido_insumo.cantidad}, disponible {pedido_insumo.insumo.stock_actual}"
                    )
            
            if insufficient_items:
                # Stock insufficient - store error for admin to handle
                error_message = "No hay suficiente stock para los siguientes insumos:\n" + "\n".join(insufficient_items)
                print(f"❌ STOCK ERROR: {error_message}")
                
                # Store the error message to show in admin
                self.instance._stock_error = error_message
                # Don't raise ValidationError - let admin handle it
                return 'aprobado'  # Keep original estado
            
            # Stock is sufficient - show confirmation message
            stock_details = []
            for pedido_insumo in self.instance.insumos.all():
                remaining = pedido_insumo.insumo.stock_actual - pedido_insumo.cantidad
                status = "CRÍTICO" if remaining <= pedido_insumo.insumo.stock_minimo * 0.5 else "BAJO" if remaining < pedido_insumo.insumo.stock_minimo else "NORMAL"
                stock_details.append(f"{pedido_insumo.insumo.nombre}: {pedido_insumo.cantidad} → {remaining} restantes ({status})")
            
            confirmation_message = (
                f"¿Está seguro de cambiar el estado a 'Orden de Trabajo'?\n\n"
                f"Impacto en el stock:\n" + "\n".join(stock_details) + "\n\n"
                f"Si está seguro, guarde nuevamente para confirmar."
            )
            
            # Store confirmation flag and show message
            self.instance._needs_confirmation = True
            self.instance._confirmation_message = confirmation_message
        
        return new_estado


class NaromiAdminSite(admin.AdminSite):
    site_header = 'Naromi Studio'
    site_title = 'Naromi Studio'
    index_title = 'Dashboard'


    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Only show Usuario model to admin users
        # Skip role check for anonymous users (they'll be redirected to login)
        if request.user.is_authenticated and hasattr(request.user, 'rol') and request.user.rol != 'admin':
            for app in app_list:
                app['models'] = [
                    model for model in app['models']
                    if model['object_name'] != 'Usuario'
                ]
        return app_list

    def index(self, request, extra_context=None):
        # Get critical stock insumos
        critical_stock_insumos = Insumo.objects.filter(
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
            'critical_stock_insumos': critical_stock_insumos,
            'critical_stock_count': critical_stock_insumos.count(),
            'active_orders_count': active_orders.count(),
            'total_insumos': Insumo.objects.count(),
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
    list_display = ('username', 'email', 'get_full_name', 'rol', 'is_active', 'is_staff', 'last_login')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_per_page = 25
    ordering = ('username',)
    
    def get_full_name(self, obj):
        """Show full name if available, otherwise show username"""
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username
    get_full_name.short_description = 'Nombre Completo'
    
    def get_queryset(self, request):
        """Optimize queryset for better performance"""
        return super().get_queryset(request).select_related()


@admin.register(Cliente, site=admin_site)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'pedidos_count')
    search_fields = ('nombre', 'email', 'telefono')
    list_filter = ('nombre',)
    list_per_page = 25
    ordering = ('nombre',)
    
    def pedidos_count(self, obj):
        """Show the number of orders for this client"""
        count = obj.pedido_set.count()
        if count > 0:
            return f"{count} pedido{'s' if count != 1 else ''}"
        return "Sin pedidos"
    pedidos_count.short_description = 'Pedidos'


@admin.register(Insumo, site=admin_site)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'stock_actual', 'stock_minimo', 'estado_stock', 'precio_unitario')
    search_fields = ('sku', 'nombre', 'descripcion')
    list_filter = ('unidad',)
    list_per_page = 25
    ordering = ('nombre',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('sku', 'nombre', 'descripcion', 'unidad')
        }),
        ('Stock y Precio', {
            'fields': ('stock_actual', 'stock_minimo', 'precio_unitario')
        }),
    )

    def estado_stock(self, obj):
        """Show stock status with color coding"""
        if obj.stock_actual <= obj.stock_minimo * 0.5:
            return 'Crítico'
        elif obj.stock_actual <= obj.stock_minimo:
            return 'Bajo'
        return 'Normal'
    estado_stock.short_description = 'Estado'
    
    def get_queryset(self, request):
        """Optimize queryset for better performance"""
        return super().get_queryset(request)
    
    def changelist_view(self, request, extra_context=None):
        """Add inventory statistics to the changelist view"""
        extra_context = extra_context or {}
        
        # Get inventory statistics
        total_insumos = Insumo.objects.count()
        stock_normal = Insumo.objects.filter(
            stock_actual__gt=F('stock_minimo')
        ).count()
        stock_bajo = Insumo.objects.filter(
            stock_actual__lte=F('stock_minimo'),
            stock_actual__gt=F('stock_minimo') * 0.5
        ).count()
        stock_critico = Insumo.objects.filter(
            stock_actual__lte=F('stock_minimo') * 0.5
        ).count()
        
        extra_context.update({
            'total_insumos': total_insumos,
            'stock_normal': stock_normal,
            'stock_bajo': stock_bajo,
            'stock_critico': stock_critico,
        })
        
        return super().changelist_view(request, extra_context)


class PedidoInsumoInline(admin.TabularInline):
    model = PedidoInsumo
    extra = 1


@admin.register(Pedido, site=admin_site)
class PedidoAdmin(admin.ModelAdmin):
    form = PedidoAdminForm
    inlines = [PedidoInsumoInline]
    list_display = ('id', 'cliente_nombre', 'estado', 'fecha', 'total', 'creado_por')
    list_filter = ('estado', 'fecha', 'cliente', 'creado_por')
    search_fields = ('cliente__nombre', 'cliente__email', 'id')
    list_per_page = 25
    ordering = ('-fecha',)
    
     # Nuevo: Añadir total, descuento, total_final y factura a la lista de lectura
    readonly_fields = ('descuento', 'total_final', 'factura_link')
    
    # Modificar fieldsets para mostrar los nuevos campos
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('cliente', 'estado', 'total', 'descuento', 'total_final', 'factura_link')
        }),
        ('Detalles Adicionales', {
            'fields': ('creado_por',),
            'classes': ('collapse',)
        }),
    )

    def factura_link(self, obj):
        """Botón para generar la factura PDF desde el admin."""
        if not obj.pk:
            return ""
        url = reverse('generar_factura_pdf', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">🧾 Imprimir factura</a>', url)
    factura_link.short_description = 'Factura'

    def cliente_nombre(self, obj):
        return obj.cliente.nombre
    cliente_nombre.short_description = 'Cliente'
    
    def changelist_view(self, request, extra_context=None):
        """Add order statistics to the changelist view"""
        extra_context = extra_context or {}
        
        # Get order statistics
        total_pedidos = Pedido.objects.count()
        pedidos_activos = Pedido.objects.exclude(
            estado__in=['completado', 'cancelado']
        ).count()
        pedidos_completados = Pedido.objects.filter(estado='completado').count()
        
        # Calculate monthly revenue
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ingresos_mes = Pedido.objects.filter(
            estado='completado',
            fecha__gte=current_month
        ).aggregate(total=Sum('total'))['total'] or 0
        
        extra_context.update({
            'total_pedidos': total_pedidos,
            'pedidos_activos': pedidos_activos,
            'pedidos_completados': pedidos_completados,
            'ingresos_mes': ingresos_mes,
        })
        
        return super().changelist_view(request, extra_context)

    def validate_stock_availability(self, pedido):
        """
        Validate if there's enough stock for all insumos in the pedido.
        Returns a tuple: (is_valid, insufficient_items, stock_impact)
        """
        insufficient_items = []
        stock_impact = []
        
        print(f"🔍 STOCK VALIDATION: Checking stock for Pedido {pedido.pk}")
        
        for pedido_insumo in pedido.insumos.all():
            insumo = pedido_insumo.insumo
            required_qty = pedido_insumo.cantidad
            current_stock = insumo.stock_actual
            remaining_stock = current_stock - required_qty
            
            print(f"   📦 {insumo.nombre} ({insumo.sku}): Required={required_qty}, Current={current_stock}, Remaining={remaining_stock}")
            
            # Check if stock is insufficient
            if required_qty > current_stock:
                insufficient_items.append({
                    'insumo': insumo,
                    'required': required_qty,
                    'available': current_stock,
                    'shortage': required_qty - current_stock
                })
            
            # Calculate stock impact (for confirmation screen)
            stock_impact.append({
                'insumo': insumo,
                'required': required_qty,
                'current_stock': current_stock,
                'remaining_stock': remaining_stock,
                'below_minimum': remaining_stock < insumo.stock_minimo,
                'critical': remaining_stock <= insumo.stock_minimo * 0.5
            })
        
        is_valid = len(insufficient_items) == 0
        
        print(f"✅ STOCK VALIDATION RESULT: {'PASS' if is_valid else 'FAIL'}")
        if insufficient_items:
            print(f"❌ Insufficient stock for {len(insufficient_items)} items")
        
        return is_valid, insufficient_items, stock_impact

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    # Refrescar cliente desde BD después de guardar
        cliente = Cliente.objects.get(pk=obj.cliente_id)
        MONTO_MINIMO = 500000

        if obj.total >= MONTO_MINIMO:
            if cliente.tiene_email:
                messages.success(
                request,
                f"✅ Se aplicó correctamente un 10% de descuento al pedido del cliente {cliente.nombre}."
            )
            else:
                messages.warning(
                request,
                f"⚠️ El pedido supera los ${MONTO_MINIMO:,.2f}, pero el cliente {cliente.nombre} no tiene email registrado."
            )    
        """
        Handle saving of Pedido with custom logic for estado changes.
        """
        # Check if there was a stock error from form validation
        if hasattr(obj, '_stock_error'):
            print(f"❌ SHOWING STOCK ERROR: {obj._stock_error}")
            self.message_user(request, obj._stock_error, level=messages.ERROR)
            # Revert estado to original and save
            obj.estado = 'aprobado'
            super().save_model(request, obj, form, change)
            return
        
        # Check if this is a confirmation save (second attempt)
        if hasattr(obj, '_needs_confirmation') and obj._needs_confirmation:
            print(f"✅ CONFIRMATION SAVE: Proceeding with estado change for Pedido {obj.pk}")
            logger.info(f"Confirmation save for Pedido {obj.pk}")
            
            # Deduct stock and track warnings
            below_minimum_warnings = []
            critical_warnings = []
            
            for pedido_insumo in obj.insumos.all():
                insumo = pedido_insumo.insumo
                old_stock = insumo.stock_actual
                insumo.stock_actual -= pedido_insumo.cantidad
                insumo.save()
                print(f"📦 Updated stock for {insumo.nombre}: {old_stock} → {insumo.stock_actual}")
                
                # Check for warnings after stock deduction
                if insumo.stock_actual <= insumo.stock_minimo * 0.5:
                    critical_warnings.append(f"{insumo.nombre}: {insumo.stock_actual} unidades (crítico)")
                elif insumo.stock_actual < insumo.stock_minimo:
                    below_minimum_warnings.append(f"{insumo.nombre}: {insumo.stock_actual} unidades (por debajo del mínimo)")
            
            # Build success message with warnings
            success_message = f"✅ Estado del Pedido {obj.pk} cambiado exitosamente a 'Orden de Trabajo'. Stock actualizado."
            
            if critical_warnings:
                success_message += f"\n\n🔴 ADVERTENCIA CRÍTICA: Los siguientes insumos quedaron con stock crítico:\n" + "\n".join(critical_warnings)
            
            if below_minimum_warnings:
                success_message += f"\n\n🟡 ADVERTENCIA: Los siguientes insumos quedaron por debajo del stock mínimo:\n" + "\n".join(below_minimum_warnings)
            
            # Show success message (with warnings if any)
            message_level = messages.WARNING if (critical_warnings or below_minimum_warnings) else messages.SUCCESS
            self.message_user(request, success_message, level=message_level)
            
            # Clear confirmation flag
            obj._needs_confirmation = False
        
        # Keep the existing logic for non-admin users (legacy)
        es_admin = request.user.rol == 'admin'
        if not es_admin and obj.estado == 'orden_trabajo':
            alertas = []
            for pedido_insumo in obj.insumos.all():
                if pedido_insumo.cantidad > pedido_insumo.insumo.stock_actual:
                    alertas.append(
                        f"{pedido_insumo.insumo.nombre}: {pedido_insumo.cantidad} "
                        f"(Stock actual: {pedido_insumo.insumo.stock_actual})"
                    )
            if alertas:
                mensaje = "Stock insuficiente para los siguientes insumos:\n" + "\n".join(alertas)
                self.message_user(request, mensaje, level=messages.WARNING)
                obj.estado = 'presupuestado'
        
        super().save_model(request, obj, form, change)