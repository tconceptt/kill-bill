from __future__ import annotations

from datetime import timedelta

from django import forms

from .models import Client, Invoice, Payment, Subscription, SubscriptionPlan


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ["name", "price_monthly", "price_annual", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "price_monthly": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "price_annual": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "company_name",
            "contact_person",
            "email",
            "phone",
            "status",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "input"}),
            "contact_person": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
            "phone": forms.TextInput(attrs={"class": "input"}),
            "status": forms.Select(attrs={}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["client", "plan", "billing_cycle", "start_date", "status"]
        widgets = {
            "client": forms.Select(attrs={}),
            "plan": forms.Select(attrs={}),
            "billing_cycle": forms.Select(attrs={}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "status": forms.Select(attrs={}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active plans by default, but allow all plans if editing
        if not self.instance.pk:  # New subscription
            self.fields["plan"].queryset = SubscriptionPlan.objects.filter(is_active=True)
        else:  # Editing existing subscription
            self.fields["plan"].queryset = SubscriptionPlan.objects.all()

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get("start_date")
        if not start_date:
            self.add_error("start_date", "Start date is required")
        return cleaned


class PaymentForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False)

    class Meta:
        model = Payment
        fields = [
            "client",
            "subscription",
            "amount",
            "payment_date",
            "payment_method",
            "status",
        ]
        widgets = {
            "client": forms.Select(attrs={}),
            "subscription": forms.Select(attrs={}),
            "amount": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "payment_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "payment_method": forms.Select(attrs={}),
            "status": forms.Select(attrs={}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subscription"].queryset = Subscription.objects.select_related("client")
        client_id = self.data.get("client") or self.initial.get("client")
        if client_id:
            try:
                client_id = int(client_id)
            except (TypeError, ValueError):
                client_id = None
        if client_id:
            self.fields["subscription"].queryset = Subscription.objects.filter(
                client_id=client_id, status=Subscription.Status.ACTIVE
            )

    def clean(self):
        cleaned = super().clean()
        subscription = cleaned.get("subscription")
        client = cleaned.get("client")
        if subscription and client and subscription.client_id != client.id:
            self.add_error("subscription", "Selected subscription does not belong to client")
        if subscription and not client:
            cleaned["client"] = subscription.client
        if not subscription:
            self.add_error("subscription", "Subscription is required")
        return cleaned


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["subscription", "issue_date", "due_date"]
        widgets = {
            "subscription": forms.Select(attrs={}),
            "issue_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
        }

    def clean(self):
        cleaned = super().clean()
        issue_date = cleaned.get("issue_date")
        due_date = cleaned.get("due_date")
        if issue_date and not due_date:
            cleaned["due_date"] = issue_date + timedelta(days=14)
        if issue_date and due_date and due_date < issue_date:
            self.add_error("due_date", "Due date cannot be before issue date")
        return cleaned

    def save(self, commit: bool = True):
        invoice: Invoice = super().save(commit=False)
        plan = invoice.subscription.plan
        if invoice.subscription.billing_cycle == Subscription.BillingCycle.MONTHLY:
            invoice.amount = plan.price_monthly
        else:
            invoice.amount = plan.price_annual
        invoice.status = Invoice.Status.UNPAID
        if commit:
            invoice.save()
        return invoice
