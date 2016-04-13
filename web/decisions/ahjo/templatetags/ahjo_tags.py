from django import template

from decisions.ahjo.models import SECTION_TYPE_MAP

register = template.Library()

@register.filter
def map_section_type(section_type):
    try:
        return SECTION_TYPE_MAP[section_type]
    except KeyError:
        return SECTION_TYPE_MAP["default"] % {"section_type": section_type}
