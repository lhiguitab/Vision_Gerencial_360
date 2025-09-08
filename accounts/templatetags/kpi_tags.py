from django import template

register = template.Library()

@register.filter
def kpi_display(kpi, value):
    """
    Template filter para mostrar el valor de un KPI formateado
    """
    return kpi.get_display_value(value)
