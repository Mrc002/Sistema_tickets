from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import PasswordChangeForm

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('registro/', views.registro, name='registro'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='auth/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path(
        'perfil/password/',
        auth_views.PasswordChangeView.as_view(
            template_name='auth/password_change.html',
            form_class=PasswordChangeForm,
            success_url=reverse_lazy('perfil'),
        ),
        name='password_change',
    ),
    path('tickets/nuevo/', views.crear_ticket, name='crear_ticket'),
    path('tickets/exportar/', views.exportar_tickets, name='exportar_tickets'),
    path('tickets/<int:ticket_id>/', views.detalle_ticket, name='detalle_ticket'),
    path('tickets/<int:ticket_id>/editar/', views.editar_ticket, name='editar_ticket'),
    path('tickets/<int:ticket_id>/asignar/', views.asignar_ticket, name='asignar_ticket'),
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path(
        'notificaciones/<int:notificacion_id>/abrir/',
        views.abrir_notificacion,
        name='abrir_notificacion',
    ),
]
