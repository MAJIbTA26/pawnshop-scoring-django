from django.contrib import admin
from .models import Client, Collateral, Application


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "created_at")


@admin.register(Collateral)
class CollateralAdmin(admin.ModelAdmin):
    list_display = ("category", "estimated_value", "condition")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "status", "proposed_loan_amount", "created_at")
    list_filter = ("status",)