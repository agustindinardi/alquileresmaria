from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroUsuarioForm
from django.contrib.auth.views import LoginView, LogoutView

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Autenticar y loguear al usuario
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f"¡Cuenta creada exitosamente! Bienvenido/a, {username}.")
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

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