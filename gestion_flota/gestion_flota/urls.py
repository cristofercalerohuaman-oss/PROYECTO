# flota_site/urls.py
from django.contrib import admin # type: ignore
from django.urls import path, include # type: ignore
from django.views.generic import RedirectView # type: ignore
from django.contrib.auth import views as auth_views # type: ignore

urlpatterns = [
    path('admin/', admin.site.urls),

    # ruta corta /login -> redirige a /accounts/login/
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=False)),

    # auth (login/logout/password reset)
    path('accounts/', include('django.contrib.auth.urls')),

    # redirigir la raíz ('/') al dashboard de la app vehiculos
    path('', RedirectView.as_view(pattern_name='vehiculos:dashboard', permanent=False)),

    # rutas de la app vehiculos (dashboard, listar, detalle, etc.)
    path('', include('vehiculos.urls')),

    # (Opcional) Si quieres, puedes definir explícitas las vistas de reset:
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
