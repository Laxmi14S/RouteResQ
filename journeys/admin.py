from django.contrib import admin
from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        "source",
        "destination",
        "transport",
        "duration_minutes",
        "price",
        "transfers",
    )

    list_filter = ("transport",)
    search_fields = ("source", "destination")