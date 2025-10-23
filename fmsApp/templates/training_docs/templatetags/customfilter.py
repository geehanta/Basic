from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dict lookup in Django templates using a variable key."""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None
