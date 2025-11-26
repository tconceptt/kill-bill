from datetime import timedelta

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from kill_bill.core.models import SiteConfiguration, Subscription
from kill_bill.core.utils import process_expiring_subscriptions, send_and_log_email


class Command(BaseCommand):
    help = "Sends automated emails for expiring and expired subscriptions, and generates invoices"

    def handle(self, *args, **options):
        today = timezone.now().date()
        config = SiteConfiguration.get_config()
        days_before = config.invoice_days_before_expiry

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Running subscription emails (invoice {days_before} days or less before expiry)"
            )
        )

        # 1. Generate invoices and send reminders for subscriptions expiring within configured days
        results = process_expiring_subscriptions(days_before)

        self.stdout.write(
            f"Found {results['subscriptions_found']} subscriptions expiring within {days_before} days"
        )

        for detail in results["details"]:
            if detail["action"] == "created":
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created invoice {detail['invoice']} for {detail['client']}"
                    )
                )
                if detail["email_sent"]:
                    self.stdout.write(
                        self.style.SUCCESS(f"  Sent invoice email to {detail['client']}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  Failed to send email to {detail['client']}")
                    )
            else:
                self.stdout.write(
                    f"  Invoice {detail['invoice']} already exists for {detail['client']}"
                )

        self.stdout.write(
            f"Summary: {results['invoices_created']} invoices created, "
            f"{results['invoices_existing']} already existed, "
            f"{results['emails_sent']} emails sent"
        )

        # 2. Expired (Yesterday) - send notification without invoice
        expired_date = today - timedelta(days=1)
        expired_subscriptions = Subscription.objects.filter(end_date=expired_date)

        self.stdout.write(
            f"\nFound {expired_subscriptions.count()} subscriptions expired on {expired_date}"
        )

        for sub in expired_subscriptions:
            self.send_email(sub, "Subscription Expired", "emails/subscription_expired")

    def send_email(self, subscription: Subscription, subject: str, template_base: str):
        """Send a generic subscription email."""
        try:
            context = {"subscription": subscription}
            html_message = render_to_string(f"{template_base}.html", context)
            plain_message = render_to_string(f"{template_base}.txt", context)

            send_and_log_email(
                subject=subject,
                message=plain_message,
                recipient_list=[subscription.client.email],
                html_message=html_message,
            )
            self.stdout.write(
                self.style.SUCCESS(f"  Sent email to {subscription.client.email}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"  Failed to send email to {subscription.client.email}: {e}"
                )
            )
