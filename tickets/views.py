import csv

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import puede_ver_ticket, rol_requerido
from .forms import (
    AsignacionForm,
    CierreForm,
    FiltroTicketsForm,
    PerfilForm,
    PrioridadForm,
    ReaperturaForm,
    RegistroForm,
    SeguimientoForm,
    TicketForm,
)
from .models import Notificacion, Seguimiento, Ticket, Usuario
from .services import (
    asignar_agente,
    notificar_cambio_estado,
    notificar_cierre,
    notificar_comentario,
    notificar_ticket_creado,
    registrar_evento,
)

PAGINA_TAMANO = 20


def _aplicar_filtros(request, qs):
    """Aplica búsqueda y filtros del listado (mejora adicional)."""
    form = FiltroTicketsForm(
        request.GET or None, mostrar_agente=request.user.es_admin
    )
    if form.is_valid():
        data = form.cleaned_data
        if data.get('q'):
            qs = qs.filter(
                Q(titulo__icontains=data['q']) | Q(descripcion__icontains=data['q'])
            )
        if data.get('estado'):
            qs = qs.filter(estado=data['estado'])
        if data.get('prioridad'):
            qs = qs.filter(prioridad=data['prioridad'])
        if data.get('agente'):
            qs = qs.filter(agente=data['agente'])
        if data.get('fecha_desde'):
            qs = qs.filter(fecha_creacion__date__gte=data['fecha_desde'])
        if data.get('fecha_hasta'):
            qs = qs.filter(fecha_creacion__date__lte=data['fecha_hasta'])
    return qs, form


def _paginar(request, qs):
    """Pagina en bloques de 20 y conserva los filtros en los enlaces."""
    page_obj = Paginator(qs, PAGINA_TAMANO).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return page_obj, params.urlencode()


@login_required
def dashboard_view(request):
    user = request.user

    if user.es_admin:
        base = Ticket.objects.select_related('cliente', 'agente')
        filtrados, filtro_form = _aplicar_filtros(request, base)
        page_obj, querystring = _paginar(request, filtrados)
        context = {
            'total': base.count(),
            'nuevos': base.filter(estado=Ticket.ESTADO_NUEVO).count(),
            'en_proceso': base.filter(estado=Ticket.ESTADO_EN_PROCESO).count(),
            'cerrados': base.filter(estado=Ticket.ESTADO_CERRADO).count(),
            'sin_asignar': base.filter(agente__isnull=True)
            .exclude(estado__in=Ticket.ESTADOS_FINALES)[:5],
            'page_obj': page_obj,
            'querystring': querystring,
            'filtro_form': filtro_form,
        }
        return render(request, 'tickets/dashboard_admin.html', context)

    if user.es_agente:
        base = Ticket.objects.filter(agente=user).select_related('cliente', 'agente')
        filtrados, filtro_form = _aplicar_filtros(request, base)
        page_obj, querystring = _paginar(request, filtrados)
        context = {
            'nuevos': base.filter(estado=Ticket.ESTADO_NUEVO).count(),
            'en_proceso': base.filter(estado=Ticket.ESTADO_EN_PROCESO).count(),
            'resueltos': base.filter(estado=Ticket.ESTADO_RESUELTO).count(),
            'page_obj': page_obj,
            'querystring': querystring,
            'filtro_form': filtro_form,
        }
        return render(request, 'tickets/dashboard_agente.html', context)

    base = Ticket.objects.filter(cliente=user).select_related('agente')
    filtrados, filtro_form = _aplicar_filtros(request, base)
    page_obj, querystring = _paginar(request, filtrados)
    return render(
        request,
        'tickets/dashboard_cliente.html',
        {
            'page_obj': page_obj,
            'querystring': querystring,
            'filtro_form': filtro_form,
        },
    )


def registro(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada correctamente. ¡Bienvenido!')
            return redirect('dashboard')
    else:
        form = RegistroForm()
    return render(request, 'auth/registro.html', {'form': form})


@rol_requerido(Usuario.ROL_CLIENTE)
def crear_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.cliente = request.user
            ticket.estado = Ticket.ESTADO_NUEVO
            ticket.save()
            registrar_evento(
                ticket,
                request.user,
                Seguimiento.TIPO_CREACION,
                'El ticket fue creado.',
            )
            notificar_ticket_creado(ticket)
            messages.success(request, f'Ticket TKT-{ticket.id:03d} creado correctamente.')
            return redirect('detalle_ticket', ticket_id=ticket.id)
    else:
        form = TicketForm()
    return render(request, 'tickets/crear_ticket.html', {'form': form})


@rol_requerido(Usuario.ROL_CLIENTE)
def editar_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id, cliente=request.user)
    if ticket.estado != Ticket.ESTADO_NUEVO:
        messages.error(request, 'Solo se puede editar un ticket en estado "Nuevo".')
        return redirect('detalle_ticket', ticket_id=ticket.id)

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            registrar_evento(
                ticket,
                request.user,
                Seguimiento.TIPO_EDICION,
                'El cliente editó el ticket.',
            )
            messages.success(request, 'Ticket actualizado correctamente.')
            return redirect('detalle_ticket', ticket_id=ticket.id)
    else:
        form = TicketForm(instance=ticket)
    return render(
        request, 'tickets/editar_ticket.html', {'form': form, 'ticket': ticket}
    )


@login_required
def detalle_ticket(request, ticket_id):
    ticket = get_object_or_404(
        Ticket.objects.select_related('cliente', 'agente'), pk=ticket_id
    )

    if not puede_ver_ticket(request.user, ticket):
        raise PermissionDenied

    user = request.user
    puede_gestionar = user.es_admin or (
        user.es_agente and ticket.agente_id == user.id
    )
    bloqueado = ticket.estado in Ticket.ESTADOS_FINALES

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # Un ticket cerrado/cancelado es de solo lectura salvo reapertura (RN-07).
        if bloqueado and accion != 'reabrir':
            messages.error(
                request, 'El ticket está cerrado o cancelado y no admite cambios.'
            )
            return redirect('detalle_ticket', ticket_id=ticket.id)

        if accion == 'comentar':
            form = SeguimientoForm(request.POST)
            if form.is_valid():
                seguimiento = form.save(commit=False)
                seguimiento.ticket = ticket
                seguimiento.usuario = user
                seguimiento.tipo = Seguimiento.TIPO_COMENTARIO
                seguimiento.es_interno = bool(
                    form.cleaned_data.get('es_interno')
                ) and (user.es_admin or user.es_agente)
                seguimiento.save()
                notificar_comentario(ticket, seguimiento)
                messages.success(request, 'Comentario agregado.')
            else:
                messages.error(request, 'El comentario no es válido.')
            return redirect('detalle_ticket', ticket_id=ticket.id)

        if accion == 'cambiar_estado':
            if not puede_gestionar:
                raise PermissionDenied
            nuevo_estado = request.POST.get('estado')
            estados_validos = {e[0] for e in Ticket.ESTADOS}
            if nuevo_estado not in estados_validos or nuevo_estado in Ticket.ESTADOS_FINALES:
                messages.error(request, 'Estado no válido para esta acción.')
            elif not ticket.puede_transicionar_a(nuevo_estado):
                messages.error(
                    request,
                    f'Transición no permitida de "{ticket.estado}" a "{nuevo_estado}".',
                )
            elif nuevo_estado == Ticket.ESTADO_ASIGNADO and not ticket.agente:
                messages.error(
                    request, 'Debes asignar un agente antes de marcar el ticket como "Asignado".'
                )
            else:
                anterior = ticket.estado
                ticket.estado = nuevo_estado
                ticket.save()
                registrar_evento(
                    ticket,
                    user,
                    Seguimiento.TIPO_ESTADO,
                    f'Estado cambiado de "{anterior}" a "{nuevo_estado}".',
                )
                notificar_cambio_estado(ticket, anterior, actor=user)
                messages.success(request, f'Estado actualizado a "{nuevo_estado}".')
            return redirect('detalle_ticket', ticket_id=ticket.id)

        if accion == 'cambiar_prioridad':
            if not puede_gestionar:
                raise PermissionDenied
            anterior = ticket.get_prioridad_display()
            form = PrioridadForm(request.POST, instance=ticket)
            if form.is_valid():
                form.save()
                registrar_evento(
                    ticket,
                    user,
                    Seguimiento.TIPO_PRIORIDAD,
                    f'Prioridad cambiada de "{anterior}" a "{ticket.get_prioridad_display()}".',
                )
                messages.success(request, 'Prioridad actualizada.')
            else:
                messages.error(request, 'Prioridad no válida.')
            return redirect('detalle_ticket', ticket_id=ticket.id)

        if accion == 'cerrar':
            if not puede_gestionar:
                raise PermissionDenied
            if not ticket.puede_transicionar_a(Ticket.ESTADO_CERRADO):
                messages.error(
                    request, f'No se puede cerrar un ticket en estado "{ticket.estado}".'
                )
                return redirect('detalle_ticket', ticket_id=ticket.id)
            form = CierreForm(request.POST)
            if form.is_valid():
                ticket.cerrar(form.cleaned_data['resolucion'])
                registrar_evento(
                    ticket,
                    user,
                    Seguimiento.TIPO_CIERRE,
                    f'Ticket cerrado. Resolución: {ticket.resolucion}',
                )
                notificar_cierre(ticket, actor=user)
                messages.success(request, 'Ticket cerrado correctamente.')
            else:
                messages.error(
                    request,
                    'La resolución es obligatoria y debe tener al menos 10 caracteres.',
                )
            return redirect('detalle_ticket', ticket_id=ticket.id)

        if accion == 'reabrir':
            if not user.es_admin:
                raise PermissionDenied
            if ticket.estado != Ticket.ESTADO_CERRADO:
                messages.error(request, 'Solo se pueden reabrir tickets cerrados.')
                return redirect('detalle_ticket', ticket_id=ticket.id)
            form = ReaperturaForm(request.POST)
            if form.is_valid():
                ticket.reabrir()
                registrar_evento(
                    ticket,
                    user,
                    Seguimiento.TIPO_REAPERTURA,
                    f'Ticket reabierto. Motivo: {form.cleaned_data["motivo"]}',
                )
                messages.success(request, 'Ticket reabierto y en proceso.')
            else:
                messages.error(
                    request, 'El motivo de reapertura debe tener al menos 10 caracteres.'
                )
            return redirect('detalle_ticket', ticket_id=ticket.id)

        if accion == 'cancelar':
            if not (user.es_cliente and ticket.cliente_id == user.id):
                raise PermissionDenied
            if ticket.estado != Ticket.ESTADO_NUEVO:
                messages.error(request, 'Solo puedes cancelar tickets en estado "Nuevo".')
            else:
                ticket.estado = Ticket.ESTADO_CANCELADO
                ticket.save()
                registrar_evento(
                    ticket,
                    user,
                    Seguimiento.TIPO_CANCELACION,
                    'El cliente canceló el ticket.',
                )
                messages.success(request, 'Ticket cancelado.')
            return redirect('detalle_ticket', ticket_id=ticket.id)

    seguimientos = ticket.seguimientos.select_related('usuario')
    if user.es_cliente:
        seguimientos = seguimientos.filter(es_interno=False)

    context = {
        'ticket': ticket,
        'seguimientos': seguimientos,
        'seguimiento_form': SeguimientoForm(),
        'cierre_form': CierreForm(),
        'reapertura_form': ReaperturaForm(),
        'prioridad_form': PrioridadForm(instance=ticket),
        'puede_gestionar': puede_gestionar,
        'puede_comentar': ticket.esta_abierto,
        'puede_cerrar': puede_gestionar
        and ticket.puede_transicionar_a(Ticket.ESTADO_CERRADO),
        'puede_reabrir': user.es_admin and ticket.estado == Ticket.ESTADO_CERRADO,
        'puede_cancelar': user.es_cliente
        and ticket.cliente_id == user.id
        and ticket.estado == Ticket.ESTADO_NUEVO,
        'puede_editar': user.es_cliente
        and ticket.cliente_id == user.id
        and ticket.estado == Ticket.ESTADO_NUEVO,
        'mostrar_interno': user.es_admin or user.es_agente,
        'estados_disponibles': [
            (valor, etiqueta)
            for valor, etiqueta in Ticket.ESTADOS
            if ticket.puede_transicionar_a(valor)
            and valor not in Ticket.ESTADOS_FINALES
        ],
    }
    return render(request, 'tickets/detalle_ticket.html', context)


@rol_requerido(Usuario.ROL_ADMIN)
def asignar_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == 'POST':
        form = AsignacionForm(request.POST)
        if form.is_valid():
            try:
                asignar_agente(ticket, form.cleaned_data['agente'], request.user)
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(
                    request,
                    f'Ticket TKT-{ticket.id:03d} asignado a {ticket.agente}.',
                )
                return redirect('detalle_ticket', ticket_id=ticket.id)
    else:
        form = AsignacionForm(instance=ticket)
    return render(request, 'tickets/asignar_ticket.html', {'form': form, 'ticket': ticket})


@rol_requerido(Usuario.ROL_ADMIN)
def exportar_tickets(request):
    qs = Ticket.objects.select_related('cliente', 'agente')
    qs, _ = _aplicar_filtros(request, qs)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tickets.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            'Código',
            'Título',
            'Categoría',
            'Prioridad',
            'Estado',
            'Cliente',
            'Agente',
            'Creado',
            'Cerrado',
        ]
    )
    for ticket in qs:
        writer.writerow(
            [
                f'TKT-{ticket.id:03d}',
                ticket.titulo,
                ticket.get_categoria_display(),
                ticket.get_prioridad_display(),
                ticket.get_estado_display(),
                ticket.cliente.email,
                ticket.agente.email if ticket.agente else '',
                ticket.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                ticket.fecha_cierre.strftime('%Y-%m-%d %H:%M')
                if ticket.fecha_cierre
                else '',
            ]
        )
    return response


@login_required
def perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'auth/perfil.html', {'form': form})


@login_required
def notificaciones(request):
    """Bandeja de notificaciones internas (campana)."""
    qs = request.user.notificaciones.select_related('ticket')

    if request.method == 'POST':
        actualizadas = qs.filter(leida=False).update(leida=True)
        if actualizadas:
            messages.success(request, 'Notificaciones marcadas como leídas.')
        return redirect('notificaciones')

    page_obj, querystring = _paginar(request, qs)
    return render(
        request,
        'notificaciones/lista.html',
        {'page_obj': page_obj, 'querystring': querystring},
    )


@login_required
def abrir_notificacion(request, notificacion_id):
    """Marca una notificación como leída y abre el ticket asociado."""
    notificacion = get_object_or_404(
        Notificacion, pk=notificacion_id, usuario=request.user
    )
    if not notificacion.leida:
        notificacion.leida = True
        notificacion.save(update_fields=['leida'])
    return redirect(notificacion.get_absolute_url())
