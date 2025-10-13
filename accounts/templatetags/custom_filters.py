from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """
    Split a string by delimiter, or return queryset items for many-to-many fields
    """
    # If it's a ManyRelatedManager (many-to-many field), return all items
    if hasattr(value, 'all'):
        return value.all()
    
    # If it's a string, split it
    if isinstance(value, str):
        return value.split(delimiter)
    
    # Otherwise return as-is
    return value


@register.filter
def has_recruiterprofile(user):
    return hasattr(user, 'recruiterprofile')

@register.filter
def has_jobseekerprofile(user):
    return hasattr(user, 'jobseekerprofile')
