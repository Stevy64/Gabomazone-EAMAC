
from .models import (SocailLinks, ContactInfo , SupportNumber , SiteSetting)


def socail_links_settings(request):
    Socail_links = SocailLinks.objects.all()
    return {
        'Socail_links': Socail_links,
    }


def contact_info_settings(request):
    contact_info = ContactInfo.objects.all()
    return {
        'contact_info': contact_info,
    }

def support_number_settings(request):
    support_number = SupportNumber.objects.all()
    return {
        'support_number': support_number,
    }    

def site_settings(request):
    site_info = SiteSetting.objects.all().first()
    return {
        'site_info': site_info,
    }      