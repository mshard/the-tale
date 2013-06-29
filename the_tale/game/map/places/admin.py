# coding: utf-8

from django.contrib import admin

from game.map.places.models import Place, Building, ResourceExchange


class PlaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'size', 'x', 'y')


class BuildingAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'integrity', 'state', 'person', 'type', 'x', 'y')


class ResourceExchangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'place_1', 'place_2', 'resource_1', 'resource_2', 'bill')


admin.site.register(Place, PlaceAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(ResourceExchange, ResourceExchangeAdmin)
