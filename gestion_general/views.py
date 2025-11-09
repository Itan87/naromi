from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template.loader import render_to_string
import tempfile
from .models import Pedido
import io
from xhtml2pdf import pisa

# -----------------------------
# AUTENTICACIÓN
# -----------------------------


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('admin:index')


class CustomLogoutView(LogoutView):
    next_page = 'login'  # Redirect to login page after logout


# Redirect root to login if not authenticated, otherwise to admin
def home(request):
    if request.user.is_authenticated:
        return redirect('admin:index')
    return redirect('login')

# -----------------------------
# FACTURA EN PDF
# -----------------------------
from django.urls import path
from . import views

def generar_factura_pdf(request, id):
    try:
        pedido = Pedido.objects.get(pk=id)
    except Pedido.DoesNotExist:
        return HttpResponse("Pedido no encontrado.", status=404)

    # Calcular total final con descuento si corresponde
    total_final = pedido.total_final if pedido.total_final else (pedido.total or 0)

    # Renderizar HTML de la factura
    html = render_to_string(
        'admin/gestion_general/pedido/factura.html',
        {
            'pedido': pedido,
            'total_final': total_final,
            'request': request
        }
    )

    # Crear PDF en memoria
    result_io = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result_io)
    
    if pdf.err:
        return HttpResponse("Error al generar PDF", status=500)
    
    # Enviar PDF como respuesta HTTP
    response = HttpResponse(result_io.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{pedido.id}.pdf"'
    return response