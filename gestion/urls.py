from django.urls import path
from gestion_general.views import home, CustomLoginView, CustomLogoutView
from gestion_general.admin import admin_site

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin_site.urls),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]