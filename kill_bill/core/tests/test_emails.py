from django.test import TestCase
from django.core import mail
from django.utils import timezone
from django.core.management import call_command
from kill_bill.core.models import Client, Subscription, SubscriptionPlan
from datetime import timedelta

class SubscriptionEmailTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            company_name="Test Company",
            contact_person="John Doe",
            email="john@example.com",
            phone="1234567890"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan",
            price_monthly=10.00,
            price_annual=100.00
        )

    def test_subscription_created_email(self):
        # Create a new subscription
        Subscription.objects.create(
            client=self.client,
            plan=self.plan,
            billing_cycle=Subscription.BillingCycle.MONTHLY,
            start_date=timezone.now().date()
        )

        # Check that one message has been sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome to Kill Bill - Subscription Created")
        self.assertEqual(mail.outbox[0].to, ["john@example.com"])
        
        # Check log
        from kill_bill.core.models import EmailLog
        self.assertEqual(EmailLog.objects.count(), 1)
        log = EmailLog.objects.first()
        self.assertEqual(log.recipient, "john@example.com")
        self.assertEqual(log.subject, "Welcome to Kill Bill - Subscription Created")
        self.assertEqual(log.status, EmailLog.Status.SENT)

    def test_subscription_expiring_soon_email(self):
        # Create a subscription expiring in 7 days
        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        start_date = end_date - timedelta(days=30)
        
        sub = Subscription.objects.create(
            client=self.client,
            plan=self.plan,
            billing_cycle=Subscription.BillingCycle.MONTHLY,
            start_date=start_date
        )
        Subscription.objects.filter(pk=sub.pk).update(end_date=end_date)
        
        # Clear outbox from creation email
        mail.outbox = []
        
        call_command('send_subscription_emails')
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Action Required: Subscription Expiring Soon")
        
        # Check log (should be 2 now, 1 from creation, 1 from command)
        from kill_bill.core.models import EmailLog
        self.assertEqual(EmailLog.objects.count(), 2)
        log = EmailLog.objects.first()
        self.assertEqual(log.recipient, "john@example.com")
        self.assertEqual(log.subject, "Action Required: Subscription Expiring Soon")

    def test_subscription_expired_email(self):
        # Create a subscription expired yesterday
        today = timezone.now().date()
        end_date = today - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        
        sub = Subscription.objects.create(
            client=self.client,
            plan=self.plan,
            billing_cycle=Subscription.BillingCycle.MONTHLY,
            start_date=start_date
        )
        Subscription.objects.filter(pk=sub.pk).update(end_date=end_date)
        
        # Clear outbox from creation email
        mail.outbox = []
        
        call_command('send_subscription_emails')
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Subscription Expired")
        
        # Check log
        from kill_bill.core.models import EmailLog
        self.assertEqual(EmailLog.objects.count(), 2)
        log = EmailLog.objects.first()
        self.assertEqual(log.recipient, "john@example.com")
        self.assertEqual(log.subject, "Subscription Expired")
