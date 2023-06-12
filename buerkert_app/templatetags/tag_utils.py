from django import template

from res.units import Units

register = template.Library()


@register.simple_tag
def resolve_unit(unit):
    return {"display": getattr(Units, unit).value[0], "unit": getattr(Units, unit).value[1]}
