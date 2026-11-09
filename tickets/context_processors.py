def notificaciones_internas(request):
    """Expone el resumen de notificaciones internas a todas las plantillas."""
    if not request.user.is_authenticated:
        return {}
    qs = request.user.notificaciones.all()
    return {
        'notificaciones_no_leidas': qs.filter(leida=False).count(),
        'notificaciones_recientes': list(qs[:5]),
    }
