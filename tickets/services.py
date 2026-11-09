"""Servicios de dominio: auditoría y notificaciones internas."""

from .models import Notificacion, Seguimiento, Ticket, Usuario


def registrar_evento(ticket, usuario, tipo, detalle, interno=False):
    """Registra un evento automático en el historial del ticket."""
    return Seguimiento.objects.create(
        ticket=ticket,
        usuario=usuario,
        tipo=tipo,
        comentario=detalle,
        es_interno=interno,
    )


def _notificar(usuario, ticket, tipo, mensaje, actor=None):
    """Crea una notificación interna evitando avisar al propio actor.

    La especificación mantiene las notificaciones 100% dentro del sistema
    (campana), sin correos electrónicos automatizados.
    """
    if usuario is None or not usuario.is_active:
        return None
    if actor is not None and usuario.pk == actor.pk:
        return None
    return Notificacion.objects.create(
        usuario=usuario,
        ticket=ticket,
        tipo=tipo,
        mensaje=mensaje,
    )


def notificar_ticket_creado(ticket):
    """Avisa a los administradores de un ticket nuevo (campana)."""
    for admin in Usuario.objects.filter(
        rol=Usuario.ROL_ADMIN, is_active=True
    ):
        _notificar(
            admin,
            ticket,
            Notificacion.TIPO_TICKET_NUEVO,
            f'Nuevo ticket {ticket}: {ticket.titulo}',
        )


def notificar_asignacion(ticket, actor=None):
    _notificar(
        ticket.agente,
        ticket,
        Notificacion.TIPO_ASIGNACION,
        f'Se te asignó el ticket {ticket}: {ticket.titulo}',
        actor=actor,
    )


def notificar_cambio_estado(ticket, estado_anterior, actor=None):
    mensaje = (
        f'El ticket {ticket} cambió de "{estado_anterior}" '
        f'a "{ticket.estado}".'
    )
    for usuario in {ticket.cliente, ticket.agente}:
        _notificar(
            usuario,
            ticket,
            Notificacion.TIPO_ESTADO,
            mensaje,
            actor=actor,
        )


def notificar_cierre(ticket, actor=None):
    mensaje = f'El ticket {ticket} fue cerrado.'
    for usuario in {ticket.cliente, ticket.agente}:
        _notificar(
            usuario,
            ticket,
            Notificacion.TIPO_CIERRE,
            mensaje,
            actor=actor,
        )


def notificar_comentario(ticket, seguimiento):
    """Avisa a los implicados cuando hay un comentario nuevo.

    Los comentarios internos solo generan aviso para el agente asignado.
    """
    if seguimiento.es_interno:
        destinatarios = [ticket.agente]
    else:
        destinatarios = list({ticket.cliente, ticket.agente})

    for destinatario in destinatarios:
        _notificar(
            destinatario,
            ticket,
            Notificacion.TIPO_COMENTARIO,
            f'{seguimiento.usuario} comentó en {ticket}.',
            actor=seguimiento.usuario,
        )


def liberar_tickets_de_agente(agente):
    """Al desactivar/eliminar un agente, deja sus tickets abiertos reasignables."""
    abiertos = Ticket.objects.filter(agente=agente).exclude(
        estado__in=Ticket.ESTADOS_FINALES
    )
    for ticket in abiertos:
        ticket.agente = None
        if ticket.estado == Ticket.ESTADO_ASIGNADO:
            ticket.estado = Ticket.ESTADO_NUEVO
        ticket.save()
        registrar_evento(
            ticket,
            agente,
            Seguimiento.TIPO_ASIGNACION,
            f'El agente {agente} fue desactivado o eliminado; el ticket quedó sin asignar.',
            interno=True,
        )


def asignar_agente(ticket, agente, usuario):
    """Asigna un agente validando rol y estado."""
    if agente is None or agente.rol != Usuario.ROL_AGENTE:
        raise ValueError('El usuario seleccionado no tiene rol de agente.')
    if ticket.estado in Ticket.ESTADOS_FINALES:
        raise ValueError('No se puede asignar un ticket cerrado o cancelado.')

    anterior = ticket.agente
    ticket.agente = agente
    if ticket.estado == Ticket.ESTADO_NUEVO:
        ticket.estado = Ticket.ESTADO_ASIGNADO
    ticket.save()

    if anterior != agente:
        registrar_evento(
            ticket,
            usuario,
            Seguimiento.TIPO_ASIGNACION,
            f'Ticket asignado a {agente}.',
        )
        notificar_asignacion(ticket, actor=usuario)
    return ticket
