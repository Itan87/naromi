from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelform_factory, inlineformset_factory
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Producto, Pedido, PedidoInsumo

def is_admin(user):
    return user.is_authenticated and user.rol == 'admin'

def is_emp(user):
    return user.is_authenticated and user.rol in ('emp', 'admin')

@login_required
def dashboard(request):
    productos = Producto.objects.order_by('nombre')
    pedidos = Pedido.objects.order_by('-fecha')[:10]
    return render(request, 'gestion_general/dashboard.html', {'productos': productos, 'pedidos': pedidos})

# ---- Productos (solo admin via app) ----
@login_required
@user_passes_test(is_admin)
def producto_list(request):
    productos = Producto.objects.all().order_by('sku')
    return render(request, 'gestion_general/producto_list.html', {'productos': productos})

@login_required
@user_passes_test(is_admin)
def producto_create(request):
    ProductoForm = modelform_factory(Producto, fields=['sku','nombre','descripcion','color','talla','unidad','stock_actual','stock_minimo','precio_unitario'])
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado.")
            return redirect('producto_list')
    else:
        form = ProductoForm()
    return render(request, 'gestion_general/producto_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def producto_edit(request, pk):
    prod = get_object_or_404(Producto, pk=pk)
    ProductoForm = modelform_factory(Producto, fields=['sku','nombre','descripcion','color','talla','unidad','stock_actual','stock_minimo','precio_unitario'])
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=prod)
        if form.is_valid():
            form.save()
            messages.success(request,"Producto actualizado.")
            return redirect('producto_list')
    else:
        form = ProductoForm(instance=prod)
    return render(request, 'gestion_general/producto_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def producto_delete(request, pk):
    prod = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        prod.delete()
        messages.success(request,"Producto eliminado.")
        return redirect('producto_list')
    return render(request, 'gestion_general/producto_confirm_delete.html', {'producto': prod})

# ---- Pedidos (empleado/admin) ----
@login_required
@user_passes_test(is_emp)
def pedido_list(request):
    pedidos = Pedido.objects.order_by('-fecha')
    return render(request, 'gestion_general/pedido_list.html', {'pedidos': pedidos})

@login_required
@user_passes_test(is_emp)
def pedido_detail(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    return render(request, 'gestion_general/pedido_detail.html', {'pedido': pedido})

@login_required
@user_passes_test(is_emp)
def pedido_nuevo(request):
    PedidoForm = modelform_factory(Pedido, fields=['cliente','estado'])
    PedidoInsumoFormset = inlineformset_factory(Pedido, PedidoInsumo, fields=['producto','cantidad'], extra=3, can_delete=True)

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        formset = PedidoInsumoFormset(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                pedido = form.save(commit=False)
                pedido.creado_por = request.user
                pedido.save()
                formset.instance = pedido
                insumos = formset.save(commit=False)

                # check stock if requesting to move to 'aprobado' or 'orden_trabajo'
                faltantes = []
                for ins in insumos:
                    if ins.producto.stock_actual < ins.cantidad:
                        faltantes.append(f"{ins.producto.nombre} (disp {ins.producto.stock_actual}, pedido {ins.cantidad})")

                if faltantes and pedido.estado in ('aprobado','orden_trabajo'):
                    messages.error(request, "No hay stock suficiente para: " + "; ".join(faltantes))
                    transaction.set_rollback(True)
                    return render(request, 'gestion_general/pedido_form.html', {'form': form, 'formset': formset, 'productos': Producto.objects.all()})

                # save insumos
                formset.save()
                # if approved / orden_trabajo -> descontar stock
                if pedido.estado in ('aprobado','orden_trabajo'):
                    for ins in pedido.insumos.all():
                        p = ins.producto
                        p.stock_actual -= ins.cantidad
                        p.save()

                messages.success(request, "Pedido creado.")
                return redirect('pedido_list')
    else:
        form = PedidoForm()
        formset = PedidoInsumoFormset()
    return render(request, 'gestion_general/pedido_form.html', {'form': form, 'formset': formset, 'productos': Producto.objects.all()})

@login_required
@user_passes_test(is_emp)
def pedido_edit(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    PedidoForm = modelform_factory(Pedido, fields=['cliente','estado'])
    PedidoInsumoFormset = inlineformset_factory(Pedido, PedidoInsumo, fields=['producto','cantidad'], extra=1, can_delete=True)

    prev_estado = pedido.estado

    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        formset = PedidoInsumoFormset(request.POST, instance=pedido)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                pedido = form.save(commit=False)
                estar_aprobado = pedido.estado in ('aprobado','orden_trabajo')
                insumos_temp = formset.save(commit=False)
                faltantes = []
                for ins in insumos_temp:
                    if ins.producto.stock_actual < ins.cantidad:
                        faltantes.append(f"{ins.producto.nombre} (disp {ins.producto.stock_actual}, pedido {ins.cantidad})")

                if faltantes and estar_aprobado:
                    messages.error(request, "No hay stock suficiente para: " + "; ".join(faltantes))
                    transaction.set_rollback(True)
                    return redirect('pedido_edit', pk=pedido.pk)

                pedido.save()
                formset.save()

                # descontar stock solo si ahora está aprobado y antes no lo estaba
                if estar_aprobado and prev_estado not in ('aprobado','orden_trabajo'):
                    for ins in pedido.insumos.all():
                        p = ins.producto
                        p.stock_actual -= ins.cantidad
                        p.save()

                messages.success(request, "Pedido actualizado.")
                return redirect('pedido_detail', pk=pedido.pk)
    else:
        form = PedidoForm(instance=pedido)
        formset = PedidoInsumoFormset(instance=pedido)
    return render(request, 'gestion_general/pedido_form.html', {'form': form, 'formset': formset, 'pedido': pedido, 'productos': Producto.objects.all()})

@login_required
@user_passes_test(is_emp)
def pedido_delete(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        # si querés, aquí podrías reponer stock si antes ya se había descontado
        pedido.delete()
        messages.success(request, "Pedido eliminado.")
        return redirect('pedido_list')
    return render(request, 'gestion_general/pedido_confirm_delete.html', {'pedido': pedido})


