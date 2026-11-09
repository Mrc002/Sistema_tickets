from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Usuario(AbstractUser):
    """Usuario personalizado con rol de negocio.

    El login se realiza mediante el campo `email`.
    """

    ROL_CLIENTE = 'cliente'
    ROL_AGENTE = 'agente'
    ROL_ADMIN = 'admin'
    ROLES = (
        (ROL_CLIENTE, 'Cliente'),
        (ROL_AGENTE, 'Agente'),
        (ROL_ADMIN, 'Administrador'),
    )

    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_CLIENTE)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.ROL_ADMIN

    @property
    def es_agente(self):
        return self.rol == self.ROL_AGENTE

    @property
    def es_cliente(self):
        return self.rol == self.ROL_CLIENTE


class Ticket(models.Model):
    PRIORIDAD_BAJA = 'Baja'
    PRIORIDAD_MEDIA = 'Media'
    PRIORIDAD_ALTA = 'Alta'
    PRIORIDADES = (
        (PRIORIDAD_BAJA, 'Baja'),
        (PRIORIDAD_MEDIA, 'Media'),
        (PRIORIDAD_ALTA, 'Alta'),
    )

    CATEGORIA_HARDWARE = 'Hardware'
    CATEGORIA_SOFTWARE = 'Software'
    CATEGORIA_RED = 'Red'
    CATEGORIA_ACCESO = 'Acceso'
    CATEGORIA_OTRO = 'Otro'
    CATEGORIAS = (
        (CATEGORIA_HARDWARE, 'Hardware'),
        (CATEGORIA_SOFTWARE, 'Software'),
        (CATEGORIA_RED, 'Red'),
        (CATEGORIA_ACCESO, 'Acceso'),
        (CATEGORIA_OTRO, 'Otro'),
    )

    ESTADO_NUEVO = 'Nuevo'
    ESTADO_ASIGNADO = 'Asignado'
    ESTADO_EN_PROCESO = 'En Proceso'
    ESTADO_RESUELTO = 'Resuelto'
    ESTADO_CERRADO = 'Cerrado'
    ESTADO_CANCELADO = 'Cancelado'
    ESTADOS = (
        (ESTADO_NUEVO, 'Nuevo'),
        (ESTADO_ASIGNADO, 'Asignado'),
        (ESTADO_EN_PROCESO, 'En Proceso'),
        (ESTADO_RESUELTO, 'Resuelto'),
        (ESTADO_CERRADO, 'Cerrado'),
        (ESTADO_CANCELADO, 'Cancelado'),
    )
    ESTADOS_FINALES = (ESTADO_CERRADO, ESTADO_CANCELADO)

    # Transiciones permitidas de la máquina de estados (RF-27).
    # El cierre se gestiona con la acción dedicada (RF-28) y la reapertura
    # solo la realiza un administrador.
    TRANSICIONES = {
        ESTADO_NUEVO: {ESTADO_ASIGNADO, ESTADO_CANCELADO, ESTADO_CERRADO},
        ESTADO_ASIGNADO: {ESTADO_EN_PROCESO, ESTADO_CANCELADO, ESTADO_CERRADO},
        ESTADO_EN_PROCESO: {ESTADO_RESUELTO, ESTADO_CANCELADO, ESTADO_CERRADO},
        ESTADO_RESUELTO: {ESTADO_EN_PROCESO, ESTADO_CERRADO},
        ESTADO_CERRADO: {ESTADO_EN_PROCESO},
        ESTADO_CANCELADO: set(),
    }

    # Horas de vencimiento (SLA) por prioridad (mejora adicional).
    SLA_HORAS = {
        PRIORIDAD_ALTA: 4,
        PRIORIDAD_MEDIA: 24,
        PRIORIDAD_BAJA: 72,
    }

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(
        max_length=20, choices=CATEGORIAS, default=CATEGORIA_OTRO
    )
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default=PRIORIDAD_MEDIA)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_NUEVO)
    cliente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='tickets_creados'
    )
    agente = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_asignados',
    )
    resolucion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    def __str__(self):
        return f"TKT-{self.id:03d} - {self.titulo}"

    @property
    def esta_abierto(self):
        return self.estado not in self.ESTADOS_FINALES

    @property
    def fecha_vencimiento(self):
        horas = self.SLA_HORAS.get(self.prioridad, 24)
        return self.fecha_creacion + timedelta(hours=horas)

    @property
    def esta_vencido(self):
        return self.esta_abierto and timezone.now() > self.fecha_vencimiento

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES.get(self.estado, set())

    def cerrar(self, resolucion):
        """Cierra el ticket guardando la resolución (RF-28)."""
        self.estado = self.ESTADO_CERRADO
        self.resolucion = resolucion
        self.fecha_cierre = timezone.now()
        self.save()

    def reabrir(self):
        """Reabre un ticket cerrado. La fecha de cierre se limpia."""
        self.estado = self.ESTADO_EN_PROCESO
        self.fecha_cierre = None
        self.save()


class Seguimiento(models.Model):
    TIPO_COMENTARIO = 'comentario'
    TIPO_CREACION = 'creacion'
    TIPO_ESTADO = 'estado'
    TIPO_PRIORIDAD = 'prioridad'
    TIPO_ASIGNACION = 'asignacion'
    TIPO_EDICION = 'edicion'
    TIPO_CIERRE = 'cierre'
    TIPO_REAPERTURA = 'reapertura'
    TIPO_CANCELACION = 'cancelacion'
    TIPOS = (
        (TIPO_COMENTARIO, 'Comentario'),
        (TIPO_CREACION, 'Creación'),
        (TIPO_ESTADO, 'Cambio de estado'),
        (TIPO_PRIORIDAD, 'Cambio de prioridad'),
        (TIPO_ASIGNACION, 'Asignación'),
        (TIPO_EDICION, 'Edición'),
        (TIPO_CIERRE, 'Cierre'),
        (TIPO_REAPERTURA, 'Reapertura'),
        (TIPO_CANCELACION, 'Cancelación'),
    )

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='seguimientos'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_COMENTARIO)
    comentario = models.TextField()
    es_interno = models.BooleanField(
        default=False, help_text='Solo visible para agentes y administradores.'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.usuario.username} en TKT-{self.ticket.id}"

    @property
    def es_sistema(self):
        return self.tipo != self.TIPO_COMENTARIO


class Notificacion(models.Model):
    """Notificación interna dentro de la aplicación (campana)."""

    TIPO_TICKET_NUEVO = 'ticket_nuevo'
    TIPO_ASIGNACION = 'asignacion'
    TIPO_ESTADO = 'estado'
    TIPO_CIERRE = 'cierre'
    TIPO_COMENTARIO = 'comentario'
    TIPOS = (
        (TIPO_TICKET_NUEVO, 'Ticket nuevo'),
        (TIPO_ASIGNACION, 'Asignación'),
        (TIPO_ESTADO, 'Cambio de estado'),
        (TIPO_CIERRE, 'Cierre'),
        (TIPO_COMENTARIO, 'Comentario'),
    )

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='notificaciones'
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notificaciones',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_ESTADO)
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        indexes = [models.Index(fields=['usuario', 'leida'])]

    def __str__(self):
        return f'{self.usuario} · {self.mensaje}'

    def get_absolute_url(self):
        if self.ticket_id:
            return reverse('detalle_ticket', args=[self.ticket_id])
        return reverse('notificaciones')
