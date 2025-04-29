# pedidos/templatetags/filtros.py
from django import template

register = template.Library()

@register.filter
def agregar_class(value, arg):
    return value.as_widget(attrs={'class': arg})