from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    """Permite el acceso solo a usuarios autenticados con alguno de los roles dados."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.rol not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def puede_ver_ticket(user, ticket):
    """Autorización a nivel de objeto para visualizar un ticket."""
    if user.es_admin:
        return True
    if user.es_agente:
        return ticket.agente_id == user.id
    return ticket.cliente_id == user.id
