from django import template

register = template.Library()

@register.filter
def dict_key(d, k):
    """Returns the value for a given key in a dictionary."""
    return d.get(k)
