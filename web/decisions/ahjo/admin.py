from django.contrib import admin

from decisions.ahjo.models import AgendaItem

class AgendaItemAdmin(admin.ModelAdmin):
    pass

admin.site.register(AgendaItem, AgendaItemAdmin)
