from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import get_reminder_invoices


class Command(BaseCommand):
    help = "Display upcoming and overdue invoices for daily reminders"

    def handle(self, *args, **options):
        today = timezone.now().date()
        upcoming, overdue = get_reminder_invoices()

        self.stdout.write(self.style.MIGRATE_HEADING(f"Reminder summary for {today}"))

        self.stdout.write(self.style.MIGRATE_LABEL("Upcoming payments:"))
        if upcoming:
            for invoice in upcoming.select_related("subscription__client"):
                client = invoice.subscription.client.company_name
                self.stdout.write(
                    f"  {invoice.invoice_number} - {client} - due {invoice.due_date} - {invoice.amount}"
                )
        else:
            self.stdout.write("  None")

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_LABEL("Overdue payments:"))
        if overdue:
            for invoice in overdue.select_related("subscription__client"):
                client = invoice.subscription.client.company_name
                days = (today - invoice.due_date).days
                self.stdout.write(
                    f"  {invoice.invoice_number} - {client} - due {invoice.due_date} - {invoice.amount} ({days} days overdue)"
                )
        else:
            self.stdout.write("  None")
