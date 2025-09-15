from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Bienvenido al Sistema de Gestión Naromi</h1><p>Funciona correctamente ✅</p>")