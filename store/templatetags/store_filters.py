from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Divide value by arg."""
    try:
        arg = float(arg)
        if arg == 0:
            return 0  # Avoid division by zero
        return float(value) / arg
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value