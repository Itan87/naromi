from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # login / logout
    path('login/', auth_views.LoginView.as_view(template_name='gestion_general/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # productos
    path('productos/', views.producto_list, name='producto_list'),
    path('producto/nuevo/', views.producto_create, name='producto_create'),
    path('producto/<int:pk>/editar/', views.producto_edit, name='producto_edit'),
    path('producto/<int:pk>/borrar/', views.producto_delete, name='producto_delete'),

    # pedidos
    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedido/nuevo/', views.pedido_nuevo, name='pedido_nuevo'),
    path('pedido/<int:pk>/', views.pedido_detail, name='pedido_detail'),
    path('pedido/<int:pk>/editar/', views.pedido_edit, name='pedido_edit'),
    path('pedido/<int:pk>/borrar/', views.pedido_delete, name='pedido_delete'),
]