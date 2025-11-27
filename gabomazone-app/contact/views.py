from django.shortcuts import render
from django.contrib import messages
from .models import MessagesList
# Create your views here.

def contact(request):

    if request.method == 'POST':
        try:
            name = request.POST['name']
            email = request.POST['email']
            phone = request.POST['phone']
            subject = request.POST['subject']
            message = request.POST['message']

            new_message =  MessagesList(
                        name = name,
                        email =email,
                        phone = phone,
                        subject = subject,
                        message = message)
            new_message.save() 
            messages.success(
                request, f'Your Message has been sent')   
        except:
            messages.warning(
                request, f'An unknown error occurred, please contact us in another way') 
    return render(request, 'contact/page-contact.html', )