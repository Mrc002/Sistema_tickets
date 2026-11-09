from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Notificacion, Seguimiento, Ticket, Usuario
from .services import liberar_tickets_de_agente


class BaseDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(
            email='admin@t.test', username='admin', password='pass12345', rol=Usuario.ROL_ADMIN
        )
        cls.agente = Usuario.objects.create_user(
            email='agente@t.test', username='agente', password='pass12345', rol=Usuario.ROL_AGENTE
        )
        cls.otro_agente = Usuario.objects.create_user(
            email='agente2@t.test', username='agente2', password='pass12345', rol=Usuario.ROL_AGENTE
        )
        cls.cliente = Usuario.objects.create_user(
            email='cliente@t.test', username='cliente', password='pass12345', rol=Usuario.ROL_CLIENTE
        )
        cls.otro_cliente = Usuario.objects.create_user(
            email='cliente2@t.test', username='cliente2', password='pass12345', rol=Usuario.ROL_CLIENTE
        )

    def login(self, user):
        self.client.login(username=user.email, password='pass12345')


class LoginTests(BaseDataMixin, TestCase):
    def test_login_por_email(self):
        self.assertTrue(self.client.login(username='cliente@t.test', password='pass12345'))

    def test_dashboard_requiere_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_registro_crea_cliente(self):
        response = self.client.post(reverse('registro'), {
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'email': 'nuevo@t.test',
            'username': 'nuevo',
            'password1': 'compleja12345',
            'password2': 'compleja12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Usuario.objects.get(email='nuevo@t.test').rol, Usuario.ROL_CLIENTE)

    def test_perfil_actualiza_nombre(self):
        self.login(self.cliente)
        response = self.client.post(reverse('perfil'), {
            'first_name': 'Carla', 'last_name': 'Actualizada',
        })
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.last_name, 'Actualizada')

    def test_cambio_password(self):
        self.login(self.cliente)
        response = self.client.post(reverse('password_change'), {
            'old_password': 'pass12345',
            'new_password1': 'nuevaClave12345',
            'new_password2': 'nuevaClave12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.login(username='cliente@t.test', password='nuevaClave12345'))


class TicketTests(BaseDataMixin, TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create(
            titulo='Problema', descripcion='Detalle del problema', prioridad=Ticket.PRIORIDAD_MEDIA,
            categoria=Ticket.CATEGORIA_SOFTWARE, estado=Ticket.ESTADO_ASIGNADO,
            cliente=self.cliente, agente=self.agente,
        )

    # --- Acceso por objeto -------------------------------------------------
    def test_cliente_no_ve_ticket_ajeno(self):
        self.login(self.otro_cliente)
        response = self.client.get(reverse('detalle_ticket', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 403)

    def test_agente_no_ve_ticket_no_asignado(self):
        self.login(self.otro_agente)
        response = self.client.get(reverse('detalle_ticket', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 403)

    def test_agente_asignado_ve_ticket(self):
        self.login(self.agente)
        response = self.client.get(reverse('detalle_ticket', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)

    # --- Creación / edición / cancelación ---------------------------------
    def test_cliente_crea_ticket_con_categoria(self):
        self.login(self.cliente)
        response = self.client.post(reverse('crear_ticket'), {
            'titulo': 'Nuevo caso', 'descripcion': 'Descripción suficiente',
            'categoria': Ticket.CATEGORIA_RED, 'prioridad': Ticket.PRIORIDAD_ALTA,
        })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(titulo='Nuevo caso')
        self.assertEqual(ticket.cliente, self.cliente)
        self.assertEqual(ticket.estado, Ticket.ESTADO_NUEVO)
        self.assertEqual(ticket.categoria, Ticket.CATEGORIA_RED)
        self.assertTrue(ticket.seguimientos.filter(tipo=Seguimiento.TIPO_CREACION).exists())

    def test_titulo_corto_rechazado(self):
        self.login(self.cliente)
        response = self.client.post(reverse('crear_ticket'), {
            'titulo': 'abc', 'descripcion': 'Descripción suficiente',
            'categoria': Ticket.CATEGORIA_OTRO, 'prioridad': Ticket.PRIORIDAD_MEDIA,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(titulo='abc').exists())

    def test_agente_no_puede_crear_ticket(self):
        self.login(self.agente)
        self.assertEqual(self.client.get(reverse('crear_ticket')).status_code, 403)

    def test_cliente_edita_ticket_nuevo(self):
        self.ticket.estado = Ticket.ESTADO_NUEVO
        self.ticket.agente = None
        self.ticket.save()
        self.login(self.cliente)
        response = self.client.post(reverse('editar_ticket', args=[self.ticket.id]), {
            'titulo': 'Título editado', 'descripcion': 'Descripción editada completa',
            'categoria': Ticket.CATEGORIA_ACCESO, 'prioridad': Ticket.PRIORIDAD_BAJA,
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.titulo, 'Título editado')

    def test_cliente_no_edita_ticket_asignado(self):
        self.login(self.cliente)
        response = self.client.get(reverse('editar_ticket', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_ASIGNADO)

    def test_cliente_cancela_ticket_nuevo(self):
        self.ticket.estado = Ticket.ESTADO_NUEVO
        self.ticket.agente = None
        self.ticket.save()
        self.login(self.cliente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cancelar',
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_CANCELADO)

    # --- Comentarios -------------------------------------------------------
    def test_comentario_crea_seguimiento(self):
        self.login(self.cliente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'comentar', 'comentario': 'Sigo esperando',
        })
        self.assertEqual(self.ticket.seguimientos.filter(tipo=Seguimiento.TIPO_COMENTARIO).count(), 1)

    def test_comentario_interno_oculto_al_cliente(self):
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'comentar', 'comentario': 'Nota interna secreta', 'es_interno': 'on',
        })
        self.login(self.cliente)
        response = self.client.get(reverse('detalle_ticket', args=[self.ticket.id]))
        self.assertNotContains(response, 'Nota interna secreta')

        self.login(self.agente)
        response = self.client.get(reverse('detalle_ticket', args=[self.ticket.id]))
        self.assertContains(response, 'Nota interna secreta')

    # --- Estados -----------------------------------------------------------
    def test_transicion_valida_asignado_a_en_proceso(self):
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cambiar_estado', 'estado': Ticket.ESTADO_EN_PROCESO,
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_EN_PROCESO)
        self.assertTrue(self.ticket.seguimientos.filter(tipo=Seguimiento.TIPO_ESTADO).exists())

    def test_transicion_invalida_rechazada(self):
        # Asignado -> Resuelto no está permitido (debe pasar por En Proceso).
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cambiar_estado', 'estado': Ticket.ESTADO_RESUELTO,
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_ASIGNADO)

    def test_cliente_no_puede_cambiar_estado(self):
        self.login(self.cliente)
        response = self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cambiar_estado', 'estado': Ticket.ESTADO_EN_PROCESO,
        })
        self.assertEqual(response.status_code, 403)
        self.ticket.refresh_from_db()
        self.assertNotEqual(self.ticket.estado, Ticket.ESTADO_EN_PROCESO)

    def test_prioridad_cambiada_por_agente(self):
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cambiar_prioridad', 'prioridad': Ticket.PRIORIDAD_ALTA,
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.prioridad, Ticket.PRIORIDAD_ALTA)
        self.assertTrue(self.ticket.seguimientos.filter(tipo=Seguimiento.TIPO_PRIORIDAD).exists())

    # --- Cierre / reapertura ----------------------------------------------
    def test_cierre_requiere_resolucion_minima(self):
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cerrar', 'resolucion': 'corta',
        })
        self.ticket.refresh_from_db()
        self.assertNotEqual(self.ticket.estado, Ticket.ESTADO_CERRADO)

        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cerrar', 'resolucion': 'Se reinició el servicio correctamente.',
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_CERRADO)
        self.assertIsNotNone(self.ticket.fecha_cierre)
        self.assertTrue(self.ticket.resolucion.startswith('Se reinició'))

    def test_ticket_cerrado_es_solo_lectura(self):
        self.ticket.cerrar('Resolución válida y suficiente.')
        self.login(self.agente)
        seguimientos_antes = self.ticket.seguimientos.count()
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'comentar', 'comentario': 'Intento tardío',
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.seguimientos.count(), seguimientos_antes)
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_CERRADO)

    def test_admin_reabre_ticket_cerrado(self):
        self.ticket.cerrar('Resolución válida y suficiente.')
        self.login(self.admin)
        response = self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'reabrir', 'motivo': 'El problema volvió a aparecer.',
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.ESTADO_EN_PROCESO)
        self.assertIsNone(self.ticket.fecha_cierre)
        self.assertTrue(self.ticket.seguimientos.filter(tipo=Seguimiento.TIPO_REAPERTURA).exists())

    def test_agente_no_puede_reabrir(self):
        self.ticket.cerrar('Resolución válida y suficiente.')
        self.login(self.agente)
        response = self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'reabrir', 'motivo': 'Intento de reapertura.',
        })
        self.assertEqual(response.status_code, 403)

    # --- Asignación --------------------------------------------------------
    def test_asignar_ticket_solo_admin(self):
        self.login(self.agente)
        self.assertEqual(
            self.client.get(reverse('asignar_ticket', args=[self.ticket.id])).status_code, 403
        )

        self.login(self.admin)
        response = self.client.post(reverse('asignar_ticket', args=[self.ticket.id]), {
            'agente': self.otro_agente.id,
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.agente, self.otro_agente)

    def test_asignar_rechaza_usuario_cliente(self):
        self.login(self.admin)
        self.client.post(reverse('asignar_ticket', args=[self.ticket.id]), {
            'agente': self.otro_cliente.id,
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.agente, self.agente)

    def test_desactivar_agente_libera_tickets(self):
        liberar_tickets_de_agente(self.agente)
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.agente)

    # --- SLA ---------------------------------------------------------------
    def test_sla_vencido(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            prioridad=Ticket.PRIORIDAD_ALTA,
            fecha_creacion=timezone.now() - timedelta(hours=5),
        )
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.esta_vencido)

    def test_sla_no_vencido(self):
        self.assertFalse(self.ticket.esta_vencido)


class ListadoTests(BaseDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(25):
            Ticket.objects.create(
                titulo=f'Ticket {i}', descripcion='Descripción de prueba',
                categoria=Ticket.CATEGORIA_OTRO, prioridad=Ticket.PRIORIDAD_MEDIA,
                estado=Ticket.ESTADO_NUEVO if i % 2 == 0 else Ticket.ESTADO_EN_PROCESO,
                cliente=cls.cliente,
            )

    def test_paginacion_20(self):
        self.login(self.cliente)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(len(response.context['page_obj'].object_list), 20)
        response = self.client.get(reverse('dashboard'), {'page': 2})
        self.assertEqual(len(response.context['page_obj'].object_list), 5)

    def test_filtro_por_estado(self):
        self.login(self.cliente)
        response = self.client.get(reverse('dashboard'), {'estado': Ticket.ESTADO_EN_PROCESO})
        self.assertTrue(all(t.estado == Ticket.ESTADO_EN_PROCESO for t in response.context['page_obj']))

    def test_exportar_csv_solo_admin(self):
        self.login(self.agente)
        self.assertEqual(self.client.get(reverse('exportar_tickets')).status_code, 403)

        self.login(self.admin)
        response = self.client.get(reverse('exportar_tickets'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        self.assertIn('TKT-', response.content.decode())


class NotificacionTests(BaseDataMixin, TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create(
            titulo='Problema', descripcion='Detalle del problema',
            categoria=Ticket.CATEGORIA_SOFTWARE, prioridad=Ticket.PRIORIDAD_MEDIA,
            estado=Ticket.ESTADO_ASIGNADO, cliente=self.cliente, agente=self.agente,
        )

    def test_asignacion_crea_notificacion_para_agente(self):
        ticket = Ticket.objects.create(
            titulo='Sin agente', descripcion='Descripción de prueba',
            categoria=Ticket.CATEGORIA_OTRO, prioridad=Ticket.PRIORIDAD_MEDIA,
            cliente=self.cliente,
        )
        self.login(self.admin)
        self.client.post(reverse('asignar_ticket', args=[ticket.id]), {
            'agente': self.otro_agente.id,
        })
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.otro_agente,
                ticket=ticket,
                tipo=Notificacion.TIPO_ASIGNACION,
            ).exists()
        )

    def test_comentario_cliente_notifica_agente(self):
        self.login(self.cliente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'comentar', 'comentario': 'Necesito ayuda con esto',
        })
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.agente,
                ticket=self.ticket,
                tipo=Notificacion.TIPO_COMENTARIO,
            ).exists()
        )

    def test_comentario_interno_no_notifica_cliente(self):
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'comentar', 'comentario': 'Nota interna secreta',
            'es_interno': 'on',
        })
        self.assertFalse(
            Notificacion.objects.filter(
                usuario=self.cliente, ticket=self.ticket
            ).exists()
        )

    def test_cambio_estado_notifica_cliente(self):
        self.login(self.agente)
        self.client.post(reverse('detalle_ticket', args=[self.ticket.id]), {
            'accion': 'cambiar_estado', 'estado': Ticket.ESTADO_EN_PROCESO,
        })
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.cliente,
                ticket=self.ticket,
                tipo=Notificacion.TIPO_ESTADO,
            ).exists()
        )

    def test_creacion_ticket_notifica_admin(self):
        self.login(self.cliente)
        self.client.post(reverse('crear_ticket'), {
            'titulo': 'Nuevo caso', 'descripcion': 'Descripción suficiente',
            'categoria': Ticket.CATEGORIA_RED, 'prioridad': Ticket.PRIORIDAD_ALTA,
        })
        ticket = Ticket.objects.get(titulo='Nuevo caso')
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.admin,
                ticket=ticket,
                tipo=Notificacion.TIPO_TICKET_NUEVO,
            ).exists()
        )

    def test_bandeja_lista_y_marca_todas_leidas(self):
        Notificacion.objects.create(
            usuario=self.cliente, ticket=self.ticket, mensaje='Mensaje de prueba'
        )
        self.login(self.cliente)
        response = self.client.get(reverse('notificaciones'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mensaje de prueba')

        self.client.post(reverse('notificaciones'))
        self.assertFalse(
            Notificacion.objects.filter(usuario=self.cliente, leida=False).exists()
        )

    def test_abrir_notificacion_marca_leida_y_redirige(self):
        notificacion = Notificacion.objects.create(
            usuario=self.cliente, ticket=self.ticket, mensaje='Abrir ticket'
        )
        self.login(self.cliente)
        response = self.client.get(
            reverse('abrir_notificacion', args=[notificacion.id])
        )
        notificacion.refresh_from_db()
        self.assertTrue(notificacion.leida)
        self.assertRedirects(
            response, reverse('detalle_ticket', args=[self.ticket.id])
        )

    def test_notificacion_de_otro_usuario_da_404(self):
        notificacion = Notificacion.objects.create(
            usuario=self.otro_cliente, ticket=self.ticket, mensaje='Ajena'
        )
        self.login(self.cliente)
        response = self.client.get(
            reverse('abrir_notificacion', args=[notificacion.id])
        )
        self.assertEqual(response.status_code, 404)
