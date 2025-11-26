from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)


def send_and_log_email(subject, message, recipient_list, html_message=None):
    """
    Sends an email and logs the result in the EmailLog model.
    """
    from .models import EmailLog

    status = EmailLog.Status.SENT
    error_message = None

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        status = EmailLog.Status.FAILED
        error_message = str(e)
        logger.error(f"Failed to send email to {recipient_list}: {e}")

    # Log for each recipient
    for recipient in recipient_list:
        EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            status=status,
            error_message=error_message
        )


def process_expiring_subscriptions(days_before_expiry: int) -> dict:
    """
    Find all subscriptions expiring within the specified number of days,
    create invoices if needed, and send invoice emails.
    
    Returns a summary dict with counts of invoices created and emails sent.
    """
    from .models import Invoice, Subscription

    today = timezone.now().date()
    expiring_date = today + timedelta(days=days_before_expiry)

    # Find subscriptions expiring within the configured days (or less)
    expiring_subscriptions = Subscription.objects.filter(
        end_date__gt=today,  # Not yet expired
        end_date__lte=expiring_date,  # Expiring within configured days or less
        status=Subscription.Status.ACTIVE,
    ).select_related("client", "plan")

    results = {
        "subscriptions_found": expiring_subscriptions.count(),
        "invoices_created": 0,
        "invoices_existing": 0,
        "emails_sent": 0,
        "emails_failed": 0,
        "details": [],
    }

    for subscription in expiring_subscriptions:
        invoice, created = create_invoice_for_subscription(subscription)
        
        if created:
            results["invoices_created"] += 1
            # Send email for newly created invoices
            email_sent = send_invoice_email(subscription, invoice)
            if email_sent:
                results["emails_sent"] += 1
            else:
                results["emails_failed"] += 1
            
            results["details"].append({
                "client": subscription.client.company_name,
                "invoice": invoice.invoice_number,
                "action": "created",
                "email_sent": email_sent,
            })
        else:
            results["invoices_existing"] += 1
            results["details"].append({
                "client": subscription.client.company_name,
                "invoice": invoice.invoice_number,
                "action": "already_exists",
                "email_sent": False,
            })

    return results


def create_invoice_for_subscription(subscription) -> tuple:
    """
    Create an invoice for the subscription if one doesn't already exist
    for the current billing period (matching due_date = end_date).
    
    Returns (invoice, created) tuple.
    """
    from .models import Invoice

    # Check if invoice already exists for this billing period
    existing_invoice = Invoice.objects.filter(
        subscription=subscription,
        due_date=subscription.end_date,
    ).first()

    if existing_invoice:
        return existing_invoice, False

    # Calculate amount based on billing cycle
    from .models import Subscription
    
    plan = subscription.plan
    if subscription.billing_cycle == Subscription.BillingCycle.MONTHLY:
        amount = plan.price_monthly
    else:
        amount = plan.price_annual

    # Create new invoice
    invoice = Invoice.objects.create(
        subscription=subscription,
        amount=amount,
        issue_date=timezone.now().date(),
        due_date=subscription.end_date,
        status=Invoice.Status.UNPAID,
    )

    return invoice, True


def send_invoice_email(subscription, invoice) -> bool:
    """
    Send invoice reminder email with invoice details and expiration warning.
    Returns True if email was sent successfully, False otherwise.
    """
    try:
        context = {"subscription": subscription, "invoice": invoice}
        html_message = render_to_string("emails/invoice_reminder.html", context)
        plain_message = render_to_string("emails/invoice_reminder.txt", context)

        send_and_log_email(
            subject=f"Invoice {invoice.invoice_number}: Subscription Renewal Due",
            message=plain_message,
            recipient_list=[subscription.client.email],
            html_message=html_message,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send invoice email to {subscription.client.email}: {e}")
        return False
