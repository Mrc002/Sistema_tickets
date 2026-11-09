from django import template

register = template.Library()


@register.filter
def slugify_estado(value):
    """'En Proceso' -> 'EnProceso' (para clases CSS de badges)."""
    return ''.join(str(value).split())
