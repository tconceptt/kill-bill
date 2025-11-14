from django.contrib import admin

from .models import Client, Invoice, Payment, Subscription, SubscriptionPlan


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("company_name", "contact_person", "email", "phone", "status")
    search_fields = ("company_name", "contact_person", "email")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_monthly", "price_annual", "is_active")
    list_filter = ("is_active",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "plan",
        "billing_cycle",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status", "billing_cycle")
    search_fields = ("client__company_name", "plan__name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "subscription",
        "amount",
        "payment_date",
        "payment_method",
        "status",
    )
    list_filter = ("payment_method", "status")
    search_fields = ("subscription__client__company_name",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "subscription",
        "amount",
        "due_date",
        "status",
    )
    list_filter = ("status",)
    search_fields = ("invoice_number", "subscription__client__company_name")
