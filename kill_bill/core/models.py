from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Tuple

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Client(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.company_name


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_annual = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class Subscription(TimeStampedModel):
    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        ANNUAL = "annual", "Annual"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.client} - {self.plan}"

    def _calculate_end_date(self) -> date:
        months = 12 if self.billing_cycle == self.BillingCycle.ANNUAL else 1
        month = self.start_date.month - 1 + months
        year = self.start_date.year + month // 12
        month = month % 12 + 1
        day = min(self.start_date.day, monthrange(year, month)[1])
        calculated = date(year, month, day) - timedelta(days=1)
        return calculated

    def _compute_status(self) -> str:
        if self.status == self.Status.CANCELLED:
            return self.Status.CANCELLED
        today = timezone.now().date()
        if self.end_date and today > self.end_date:
            return self.Status.EXPIRED
        return self.Status.ACTIVE

    def save(self, *args, **kwargs):
        if self.start_date:
            self.end_date = self._calculate_end_date()
        self.status = self._compute_status()
        super().save(*args, **kwargs)

    @property
    def is_expiring_soon(self) -> bool:
        if not self.end_date or self.status != self.Status.ACTIVE:
            return False
        today = timezone.now().date()
        return today <= self.end_date <= today + timedelta(days=30)


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CHEQUE = "cheque", "Cheque"

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PENDING = "pending", "Pending"

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RECEIVED
    )

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Payment {self.amount} for {self.subscription}"


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="invoices"
    )
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UNPAID
    )
    last_reminder_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self) -> str:  # pragma: no cover
        return self.invoice_number

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        self.status = self.compute_status()
        super().save(*args, **kwargs)

    def compute_status(self) -> str:
        if self.status == self.Status.PAID:
            return self.Status.PAID
        today = timezone.now().date()
        if self.due_date and today > self.due_date:
            return self.Status.OVERDUE
        return self.Status.UNPAID

    @classmethod
    def generate_invoice_number(cls) -> str:
        last_invoice = cls.objects.order_by("-id").first()
        next_number = 1
        if last_invoice and last_invoice.invoice_number:
            try:
                next_number = int(last_invoice.invoice_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                next_number = last_invoice.id + 1
        return f"INV-{next_number:04d}"

    @property
    def days_overdue(self) -> int:
        if self.status != self.Status.OVERDUE:
            return 0
        return (timezone.now().date() - self.due_date).days


ReminderSummary = Tuple[models.QuerySet["Invoice"], models.QuerySet["Invoice"]]


def get_reminder_invoices() -> ReminderSummary:
    today = timezone.now().date()
    upcoming = Invoice.objects.filter(
        status__in=[Invoice.Status.UNPAID, Invoice.Status.OVERDUE],
        due_date__range=(today, today + timedelta(days=7)),
    )
    overdue = Invoice.objects.filter(
        status__in=[Invoice.Status.UNPAID, Invoice.Status.OVERDUE],
        due_date__lt=today,
    )
    return upcoming, overdue
