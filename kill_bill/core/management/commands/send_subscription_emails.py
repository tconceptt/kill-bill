from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from kill_bill.core.utils import send_and_log_email
from kill_bill.core.models import Subscription
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sends automated emails for expiring and expired subscriptions'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # 1. Expiring Soon (7 days from now)
        expiring_date = today + timedelta(days=7)
        expiring_subscriptions = Subscription.objects.filter(
            end_date=expiring_date,
            status=Subscription.Status.ACTIVE
        )
        
        self.stdout.write(f"Found {expiring_subscriptions.count()} subscriptions expiring on {expiring_date}")
        
        for sub in expiring_subscriptions:
            self.send_email(
                sub,
                "Action Required: Subscription Expiring Soon",
                "emails/subscription_expiring"
            )

        # 2. Expired (Yesterday)
        expired_date = today - timedelta(days=1)
        expired_subscriptions = Subscription.objects.filter(
            end_date=expired_date
        )
        
        self.stdout.write(f"Found {expired_subscriptions.count()} subscriptions expired on {expired_date}")
        
        for sub in expired_subscriptions:
            self.send_email(
                sub,
                "Subscription Expired",
                "emails/subscription_expired"
            )

    def send_email(self, subscription, subject, template_base):
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
            self.stdout.write(self.style.SUCCESS(f"Sent email to {subscription.client.email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email to {subscription.client.email}: {e}"))
