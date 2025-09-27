from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """Split a string by delimiter and return a list."""
    if value:
        return [item.strip() for item in value.split(delimiter)]
    return []