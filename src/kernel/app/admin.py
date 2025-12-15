from django.contrib import admin

from .models import Operator, Region, Phone


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ("id", "begin", "end", "operator", "region")
    list_select_related = ("operator", "region")
    list_filter = ("operator", "region")
    search_fields = ("begin", "end", "operator__name", "region__name")
    ordering = ("begin",)
    list_per_page = 100
