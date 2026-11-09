from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied

from .models import Notificacion, Seguimiento, Ticket, Usuario
from .services import liberar_tickets_de_agente


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Rol de negocio', {'fields': ('rol',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Rol de negocio', {'fields': ('rol', 'email')}),
    )

    def save_model(self, request, obj, form, change):
        # RF-11: el admin no puede quitarse su propio rol.
        if change and obj.pk == request.user.pk and obj.rol != Usuario.ROL_ADMIN:
            obj.rol = Usuario.ROL_ADMIN
            self.message_user(
                request,
                'No puedes quitarte el rol de administrador a ti mismo.',
                level=messages.ERROR,
            )
        super().save_model(request, obj, form, change)
        # RF-12: liberar tickets si el agente fue desactivado.
        if not obj.is_active:
            liberar_tickets_de_agente(obj)

    def delete_model(self, request, obj):
        # RF-11: el admin no puede eliminar su propia cuenta.
        if obj.pk == request.user.pk:
            raise PermissionDenied('No puedes eliminar tu propia cuenta.')
        # RF-12: liberar tickets antes de eliminar al agente.
        liberar_tickets_de_agente(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # RF-11: excluir la propia cuenta del borrado masivo.
        if queryset.filter(pk=request.user.pk).exists():
            queryset = queryset.exclude(pk=request.user.pk)
            self.message_user(
                request,
                'Tu propia cuenta fue excluida del borrado.',
                level=messages.WARNING,
            )
        # RF-12: liberar tickets de los agentes eliminados.
        for usuario in queryset:
            liberar_tickets_de_agente(usuario)
        super().delete_queryset(request, queryset)


class SeguimientoInline(admin.TabularInline):
    model = Seguimiento
    extra = 0
    readonly_fields = ('fecha',)
    fields = ('tipo', 'usuario', 'comentario', 'es_interno', 'fecha')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'titulo',
        'categoria',
        'cliente',
        'agente',
        'prioridad',
        'estado',
        'fecha_creacion',
    )
    list_filter = ('estado', 'prioridad', 'categoria')
    search_fields = ('titulo', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    inlines = [SeguimientoInline]


@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'tipo', 'usuario', 'es_interno', 'fecha')
    list_filter = ('tipo', 'es_interno', 'fecha')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'ticket', 'leida', 'fecha')
    list_filter = ('tipo', 'leida', 'fecha')
    search_fields = ('mensaje', 'usuario__email')
