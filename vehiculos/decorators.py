# vehiculos/decorators.py
from django.shortcuts import redirect
from django.contrib import messages

def admin_o_logistica_required(function):
    """
    Decorador para vistas que solo pueden ver staff o roles que NO sean 'chofer'.
    """
    def wrap(request, *args, **kwargs):
        # Si el usuario no está logueado, lo mandamos al login
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para ver esta página.')
            return redirect('login') # Asumo que tu URL de login se llama 'login'
            
        # Si el usuario es 'staff' (admin, como "cristofer"), puede pasar.
        if request.user.is_staff:
            return function(request, *args, **kwargs)
            
        # Si no es staff, revisamos su perfil y rol
        perfil = getattr(request.user, 'perfil', None)
        
        if perfil and perfil.rol != 'chofer':
            # Si tiene perfil Y su rol NO es 'chofer', puede pasar
            return function(request, *args, **kwargs)
        
        # Si llega hasta aquí, es un 'chofer' o no tiene rol. No puede pasar.
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('vehiculos:dashboard') # Lo mandamos a su dashboard

    return wrap