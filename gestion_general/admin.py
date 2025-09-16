from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Producto, Pedido, PedidoInsumo

# --- USUARIO ---
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol', {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')

# --- PRODUCTO ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'color', 'talla', 'stock_actual', 'stock_minimo')
    search_fields = ('sku', 'nombre', 'color')
    list_filter = ('color', 'talla')

# --- PEDIDOINSUMO INLINE ---
class PedidoInsumoInline(admin.TabularInline):
    model = PedidoInsumo
    extra = 1

class PedidoAdminForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'estado', 'creado_por', 'total']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # ahora sí guardamos el request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        estado_nuevo = cleaned_data.get('estado')

        if estado_nuevo == 'orden_trabajo':
            alertas = []
            for insumo in self.instance.insumos.all():
                if insumo.cantidad > insumo.producto.stock_actual:
                    alertas.append(
                        f"{insumo.producto.nombre}: pedido {insumo.cantidad}, stock {insumo.producto.stock_actual}"
                    )

            if alertas:
                raise forms.ValidationError(
                    "No hay stock suficiente para pasar a 'Orden de Trabajo':\n" + "\n".join(alertas)
                )

        return cleaned_data

# --- ADMIN DE PEDIDO ---
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [PedidoInsumoInline]
    list_display = ('id', 'cliente', 'estado', 'tipo_pedido', 'fecha')
    list_filter = ('estado', 'tipo_pedido', 'fecha')
    form = PedidoAdminForm

    def get_form(self, request, obj=None, **kwargs):
        """
        Sobrescribimos get_form para pasar el request al formulario
        y así permitir que clean() acceda a los datos.
        """
        form_class = super().get_form(request, obj, **kwargs)

        class FormWithRequest(form_class):
            def init(self2, *args, **kw):
                kw['request'] = request
                super().init(*args, **kw)

        return FormWithRequest
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.estado == 'orden_trabajo':
            faltantes = []
            for insumo in obj.insumos.all():
                if insumo.cantidad > insumo.producto.stock_actual:
                    faltantes.append((insumo.producto, insumo.cantidad))

            if faltantes:
                obj.estado = 'presupuestado'
                obj.save()

                # Creamos pedido de insumo automático
                solicitud = Pedido.objects.create(
                    tipo_pedido='insumo',
                    cliente=f"Auto-solicitud para Pedido {obj.id}",
                    estado='ingresado',
                    creado_por=request.user
                )

                for producto, cantidad in faltantes:
                    cantidad_a_pedir = cantidad - producto.stock_actual
                    PedidoInsumo.objects.create(
                        pedido=solicitud,
                        producto=producto,
                        cantidad=cantidad_a_pedir
                    )

                messages.warning(request,
                    f"⚠️ Stock insuficiente. Pedido {obj.id} se pasó a 'Presupuestado' y se creó una solicitud de insumos."
                )
            else:
                # Descontar stock si hay suficiente
                for insumo in obj.insumos.all():
                    producto = insumo.producto
                    producto.stock_actual -= insumo.cantidad
                    producto.save()
                messages.success(request, f"✅ Pedido {obj.id} confirmado y stock actualizado.")