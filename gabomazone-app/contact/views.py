import logging

from django.shortcuts import render
from django.contrib import messages

from .models import MessagesList

logger = logging.getLogger(__name__)


def contact(request):
    """Page de contact — enregistre le message en base de données."""
    if request.method == 'POST':
        try:
            name = request.POST['name']
            email = request.POST['email']
            phone = request.POST['phone']
            subject = request.POST['subject']
            message = request.POST['message']

            new_message = MessagesList(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
            )
            new_message.save()
            messages.success(request, 'Your Message has been sent')
        except Exception:
            logger.exception("Error saving contact message")
            messages.warning(request, 'An unknown error occurred, please contact us in another way')
    return render(request, 'contact/page-contact.html')
