from django import template

register = template.Library()


@register.filter
def has_perm(user, perm_string):
    """
    Usage in template: {% if user|has_perm:"products.edit" %}
    """
    if user.is_superuser:
        return True
    
    try:
        module, action = perm_string.split('.')
        return user.has_permission(module, action)
    except (ValueError, AttributeError):
        return False


@register.simple_tag
def user_can(user, module, action):
    """
    Usage in template: {% user_can user "products" "edit" as can_edit %}
    """
    if user.is_superuser:
        return True
    return user.has_permission(module, action)
