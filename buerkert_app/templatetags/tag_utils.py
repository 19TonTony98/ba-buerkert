from django import template

from res.units import Units

register = template.Library()


@register.simple_tag
def resolve_unit(unit):
    """
    :param unit: The name of the unit to resolve.
    :return: A dictionary with the display name and unit symbol for the given unit.
    """
    return {"display": getattr(Units, unit).value[0], "unit": getattr(Units, unit).value[1]}
