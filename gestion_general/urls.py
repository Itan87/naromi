from django.urls import path
from . import views

urlpatterns = [
    path('factura/<int:id>/', views.generar_factura_pdf, name='generar_factura_pdf'),
]