
from django.contrib import admin
from django.urls import path
from gestion_general.views import home

# Customize admin site
admin.site.site_header = 'Naromi Studio'
admin.site.site_title = 'Naromi Admin'
admin.site.index_title = 'Panel de Administración'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
]
