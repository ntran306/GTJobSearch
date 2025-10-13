from django import template

register = template.Library()

@register.filter
def has_recruiterprofile(user):
    return hasattr(user, 'recruiterprofile')

@register.filter
def has_jobseekerprofile(user):
    return hasattr(user, 'jobseekerprofile')
