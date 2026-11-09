from django.core.management.base import BaseCommand
from django.db import transaction

from tickets.models import Seguimiento, Ticket, Usuario
from tickets.services import notificar_asignacion, notificar_ticket_creado


class Command(BaseCommand):
    help = 'Crea datos de ejemplo (admin, agentes, clientes y tickets).'

    PASSWORDS = {
        'admin@mesa.test': 'admin12345',
        'agente1@mesa.test': 'agente12345',
        'agente2@mesa.test': 'agente12345',
        'cliente1@mesa.test': 'cliente12345',
        'cliente2@mesa.test': 'cliente12345',
        'cliente3@mesa.test': 'cliente12345',
    }

    @transaction.atomic
    def handle(self, *args, **options):
        def upsert(email, username, rol, first, last, is_staff=False, is_super=False):
            user, created = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'rol': rol,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': is_staff,
                    'is_superuser': is_super,
                },
            )
            user.rol = rol
            user.first_name = first
            user.last_name = last
            user.is_staff = is_staff
            user.is_superuser = is_super
            user.set_password(self.PASSWORDS[email])
            user.save()
            estado = 'creado' if created else 'actualizado'
            self.stdout.write(f'  {estado}: {email} ({rol})')
            return user

        self.stdout.write('Usuarios:')
        admin = upsert('admin@mesa.test', 'admin', Usuario.ROL_ADMIN, 'Admin', 'Principal',
                       is_staff=True, is_super=True)
        agente1 = upsert('agente1@mesa.test', 'agente1', Usuario.ROL_AGENTE, 'Ana', 'Agente')
        agente2 = upsert('agente2@mesa.test', 'agente2', Usuario.ROL_AGENTE, 'Bruno', 'Soporte')
        cliente1 = upsert('cliente1@mesa.test', 'cliente1', Usuario.ROL_CLIENTE, 'Carla', 'Cliente')
        cliente2 = upsert('cliente2@mesa.test', 'cliente2', Usuario.ROL_CLIENTE, 'Diego', 'Cliente')
        upsert('cliente3@mesa.test', 'cliente3', Usuario.ROL_CLIENTE, 'Elena', 'Cliente')

        if Ticket.objects.exists():
            self.stdout.write('Ya existen tickets; no se generan datos nuevos.')
            return

        self.stdout.write('Tickets:')
        demos = [
            ('No puedo iniciar sesión', 'Al intentar entrar me dice contraseña incorrecta.', Ticket.CATEGORIA_ACCESO, Ticket.PRIORIDAD_ALTA, Ticket.ESTADO_EN_PROCESO, cliente1, agente1),
            ('Impresora no imprime', 'La impresora de recepción no responde.', Ticket.CATEGORIA_HARDWARE, Ticket.PRIORIDAD_MEDIA, Ticket.ESTADO_ASIGNADO, cliente2, agente2),
            ('Solicitud de acceso a carpeta', 'Necesito acceso a la carpeta de proyectos.', Ticket.CATEGORIA_ACCESO, Ticket.PRIORIDAD_BAJA, Ticket.ESTADO_NUEVO, cliente1, None),
            ('Sistema de facturación lento', 'El sistema tarda mucho en cargar.', Ticket.CATEGORIA_SOFTWARE, Ticket.PRIORIDAD_ALTA, Ticket.ESTADO_NUEVO, cliente2, None),
            ('Correo con errores de envío', 'Los correos rebotan al enviar adjuntos.', Ticket.CATEGORIA_RED, Ticket.PRIORIDAD_MEDIA, Ticket.ESTADO_RESUELTO, cliente1, agente1),
        ]
        for titulo, desc, categoria, prioridad, estado, cliente, agente in demos:
            ticket = Ticket.objects.create(
                titulo=titulo, descripcion=desc, categoria=categoria,
                prioridad=prioridad, estado=estado, cliente=cliente, agente=agente,
            )
            Seguimiento.objects.create(ticket=ticket, usuario=cliente, comentario='Reporto el problema.')
            if agente:
                Seguimiento.objects.create(ticket=ticket, usuario=agente, comentario='Estoy revisando el caso.')
            self.stdout.write(f'  creado: {ticket}')

        cerrado = Ticket.objects.create(
            titulo='Reinicio de equipo', descripcion='El equipo se reinicia solo.',
            categoria=Ticket.CATEGORIA_HARDWARE,
            prioridad=Ticket.PRIORIDAD_MEDIA, estado=Ticket.ESTADO_CERRADO,
            cliente=cliente1, agente=agente1,
        )
        cerrado.cerrar('Se reemplazó la fuente de poder y se actualizó el firmware.')
        plugin_creds = Ticket.objects.create(
            titulo='Solicitud de alta de usuario',
            descripcion='Alta de usuario nuevo en el sistema.',
            categoria=Ticket.CATEGORIA_ACCESO,
            prioridad=Ticket.PRIORIDAD_BAJA, estado=Ticket.ESTADO_ASIGNADO,
            cliente=cliente2, agente=agente2,
        )
        self.stdout.write(f'  creado: {cerrado}')
        self.stdout.write(f'  creado: {plugin_creds}')

        for ticket in Ticket.objects.all():
            notificar_ticket_creado(ticket)
            if ticket.agente_id:
                notificar_asignacion(ticket)
        self.stdout.write('Notificaciones internas generadas.')

        self.stdout.write(self.style.SUCCESS('\nDatos de ejemplo creados.'))
        self.stdout.write('Credenciales:')
        for email, pwd in self.PASSWORDS.items():
            self.stdout.write(f'  {email} / {pwd}')
        _ = admin
