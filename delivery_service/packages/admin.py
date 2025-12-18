from django.contrib import admin

from .models import Package, PackageType


@admin.register(PackageType)
class PackageTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_package_id",
        "name",
        "package_type",
        "weight_kg",
        "content_price_usd",
        "delivery_price_rub",
        "created_at",
    )
    list_filter = ("package_type", "created_at")
    search_fields = ("name", "session_key")
    readonly_fields = ("session_key", "session_package_id", "created_at", "updated_at")
    date_hierarchy = "created_at"  # Register your models here.
