from django.core.mail import send_mail
from django.conf import settings
from .models import EmailLog
import logging

logger = logging.getLogger(__name__)

def send_and_log_email(subject, message, recipient_list, html_message=None):
    """
    Sends an email and logs the result in the EmailLog model.
    """
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
