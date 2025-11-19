from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from .utils import send_and_log_email
from .models import Subscription

@receiver(post_save, sender=Subscription)
def send_subscription_created_email(sender, instance, created, **kwargs):
    if created:
        subject = "Welcome to Kill Bill - Subscription Created"
        context = {"subscription": instance}
        
        html_message = render_to_string("emails/subscription_created.html", context)
        plain_message = render_to_string("emails/subscription_created.txt", context)
        
        send_and_log_email(
            subject=subject,
            message=plain_message,
            recipient_list=[instance.client.email],
            html_message=html_message,
        )
