from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy


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