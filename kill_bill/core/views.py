from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClientForm, InvoiceForm, PaymentForm, SubscriptionForm, SubscriptionPlanForm
from .models import Client, Invoice, Payment, Subscription, SubscriptionPlan, get_reminder_invoices


class AdminLoginView(LoginView):
    template_name = "auth/login.html"


@login_required
def dashboard(request):
    today = timezone.now().date()
    active_subscriptions = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE
    ).count()
    expiring_soon_qs = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        end_date__range=(today, today + timedelta(days=30)),
    )
    expiring_count = expiring_soon_qs.count()
    overdue_invoices_qs = Invoice.objects.filter(status=Invoice.Status.OVERDUE)
    overdue_total = overdue_invoices_qs.count()
    overdue_sum = overdue_invoices_qs.aggregate(total=models.Sum("amount"))["total"] or 0

    context = {
        "active_subscriptions": active_subscriptions,
        "expiring_count": expiring_count,
        "overdue_total": overdue_total,
        "overdue_sum": overdue_sum,
        "expiring_soon": expiring_soon_qs.select_related("client", "plan"),
        "overdue_invoices": overdue_invoices_qs.select_related("subscription__client"),
    }
    return render(request, "dashboard.html", context)


@login_required
def client_list(request):
    search = request.GET.get("search", "")
    clients = Client.objects.all()
    if search:
        clients = clients.filter(company_name__icontains=search)
    clients = clients.order_by("company_name")
    return render(request, "clients/list.html", {"clients": clients, "search": search})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Client created successfully")
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(request, "clients/form.html", {"form": form, "title": "New Client"})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated successfully")
            return redirect("client_detail", pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(
        request,
        "clients/form.html",
        {"form": form, "title": f"Edit {client.company_name}"},
    )


@login_required
def client_detail(request, pk):
    client = get_object_or_404(
        Client.objects.prefetch_related("subscriptions", "subscriptions__plan"), pk=pk
    )
    subscriptions = client.subscriptions.select_related("plan").all()
    payments = Payment.objects.filter(subscription__client=client).select_related(
        "subscription"
    )
    return render(
        request,
        "clients/detail.html",
        {"client": client, "subscriptions": subscriptions, "payments": payments},
    )


@login_required
def subscription_list(request):
    filter_value = request.GET.get("status")
    today = timezone.now().date()
    subscriptions = Subscription.objects.select_related("client", "plan")
    if filter_value == "active":
        subscriptions = subscriptions.filter(status=Subscription.Status.ACTIVE)
    elif filter_value == "expiring":
        subscriptions = subscriptions.filter(
            status=Subscription.Status.ACTIVE,
            end_date__range=(today, today + timedelta(days=30)),
        )
    elif filter_value == "expired":
        subscriptions = subscriptions.filter(status=Subscription.Status.EXPIRED)
    subscriptions = subscriptions.order_by("-start_date")
    return render(
        request,
        "subscriptions/list.html",
        {"subscriptions": subscriptions, "filter": filter_value},
    )


@login_required
def subscription_create(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, "Subscription created successfully")
            return redirect("subscription_detail", pk=subscription.pk)
    else:
        form = SubscriptionForm()
    return render(
        request,
        "subscriptions/form.html",
        {"form": form, "title": "New Subscription"},
    )


@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(
        Subscription.objects.select_related("client", "plan"), pk=pk
    )
    invoices = subscription.invoices.select_related("subscription__client")
    payments = subscription.payments.all()
    return render(
        request,
        "subscriptions/detail.html",
        {
            "subscription": subscription,
            "invoices": invoices,
            "payments": payments,
        },
    )


@login_required
def payment_list(request):
    payments = Payment.objects.select_related("subscription__client")
    client_id = request.GET.get("client")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if client_id:
        payments = payments.filter(subscription__client_id=client_id)
    if start_date:
        payments = payments.filter(payment_date__gte=start_date)
    if end_date:
        payments = payments.filter(payment_date__lte=end_date)

    payments = payments.order_by("-payment_date")
    clients = Client.objects.order_by("company_name")
    return render(
        request,
        "payments/list.html",
        {
            "payments": payments,
            "clients": clients,
            "selected_client": client_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@login_required
def payment_create(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment recorded successfully")
            return redirect("payment_list")
    else:
        initial = {}
        subscription_id = request.GET.get("subscription")
        if subscription_id:
            try:
                subscription = Subscription.objects.get(pk=subscription_id)
                initial = {"subscription": subscription, "client": subscription.client}
            except Subscription.DoesNotExist:
                pass
        form = PaymentForm(initial=initial)
    return render(
        request,
        "payments/form.html",
        {"form": form, "title": "Record Payment"},
    )


@login_required
def invoice_list(request):
    status_filter = request.GET.get("status")
    invoices = Invoice.objects.select_related("subscription__client")
    if status_filter in {Invoice.Status.UNPAID, Invoice.Status.PAID, Invoice.Status.OVERDUE}:
        invoices = invoices.filter(status=status_filter)
    elif status_filter == "overdue":
        invoices = invoices.filter(status=Invoice.Status.OVERDUE)
    invoices = invoices.order_by("-issue_date")
    return render(
        request,
        "invoices/list.html",
        {"invoices": invoices, "status_filter": status_filter},
    )


@login_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            messages.success(request, "Invoice generated successfully")
            return redirect("invoice_detail", pk=invoice.pk)
    else:
        initial = {}
        subscription_id = request.GET.get("subscription")
        if subscription_id:
            try:
                subscription = Subscription.objects.get(pk=subscription_id)
                initial = {"subscription": subscription}
            except Subscription.DoesNotExist:
                pass
        form = InvoiceForm(initial=initial)
    return render(
        request,
        "invoices/form.html",
        {"form": form, "title": "New Invoice"},
    )


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("subscription__client", "subscription__plan"), pk=pk
    )
    return render(request, "invoices/print.html", {"invoice": invoice})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("subscription__client"), pk=pk
    )
    return render(request, "invoices/detail.html", {"invoice": invoice})


@login_required
def invoice_mark_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        if invoice.status != Invoice.Status.PAID:
            invoice.status = Invoice.Status.PAID
            invoice.last_reminder_sent_at = timezone.now()
            invoice.save()
            Payment.objects.create(
                subscription=invoice.subscription,
                amount=invoice.amount,
                payment_date=timezone.now().date(),
                payment_method=Payment.Method.BANK_TRANSFER,
                status=Payment.Status.RECEIVED,
            )
            messages.success(request, "Invoice marked as paid and payment recorded")
        else:
            messages.info(request, "Invoice already marked as paid")
    return redirect("invoice_detail", pk=invoice.pk)


@login_required
def reminders(request):
    upcoming, overdue = get_reminder_invoices()
    return render(
        request,
        "reminders.html",
        {
            "upcoming": upcoming.select_related("subscription__client"),
            "overdue": overdue.select_related("subscription__client"),
        },
    )


@login_required
def plan_list(request):
    plans = SubscriptionPlan.objects.all().order_by("name")
    return render(request, "plans/list.html", {"plans": plans})


@login_required
def plan_create(request):
    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription plan created successfully")
            return redirect("plan_list")
    else:
        form = SubscriptionPlanForm()
    return render(request, "plans/form.html", {"form": form, "title": "New Subscription Plan"})


@login_required
def plan_edit(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription plan updated successfully")
            return redirect("plan_detail", pk=plan.pk)
    else:
        form = SubscriptionPlanForm(instance=plan)
    return render(
        request,
        "plans/form.html",
        {"form": form, "title": f"Edit {plan.name}", "plan": plan},
    )


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(SubscriptionPlan, pk=pk)
    subscriptions = Subscription.objects.filter(plan=plan).select_related("client")
    active_count = subscriptions.filter(status=Subscription.Status.ACTIVE).count()
    return render(
        request,
        "plans/detail.html",
        {"plan": plan, "subscriptions": subscriptions, "active_count": active_count},
    )


@login_required
def email_log_list(request):
    from .models import EmailLog
    email_logs = EmailLog.objects.all()
    return render(request, "emails/list.html", {"email_logs": email_logs})
