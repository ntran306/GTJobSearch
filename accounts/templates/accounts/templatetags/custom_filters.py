from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """
    Split a string into a list by the given delimiter.
    Usage: {{ value|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]
