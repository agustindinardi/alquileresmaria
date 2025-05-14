from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserForm, PerfilForm
from django.contrib.auth.views import LoginView, LogoutView

def registro(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        perfil_form = PerfilForm(request.POST)
        if user_form.is_valid() and perfil_form.is_valid():
            user = user_form.save()
            perfil = perfil_form.save(commit=False)
            perfil.usuario = user   # Asignar el usuario al perfil
            perfil.save()
            login(request, user)
            messages.success(request, f"¡Cuenta creada exitosamente! Bienvenido/a, {user.username}.")
            return redirect('home')
    else:
        user_form = UserForm()
        perfil_form = PerfilForm()
        
    return render(request, 'usuarios/registro.html', {'user_form': user_form, 'perfil_form': perfil_form})

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    
    def get_success_url(self):
        messages.success(self.request, f"¡Bienvenido/a de nuevo, {self.request.user.username}!")
        return super().get_success_url()

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Has cerrado sesion exitosamente.")
        return super().dispatch(request, *args, **kwargs)

@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html')