from email import message
import imp
from django.shortcuts import render
from .models import Newsletter
from django.http import JsonResponse
# Create your views here.

def letter(request):
    if request.method == "POST" and request.POST.get("value") != None and request.POST.get("value") != "" :
        value = request.POST.get("value")
        if not Newsletter.objects.all().filter(email=value).exists(): 
            Newsletter.objects.create(email=value,)
            message="Subscribe to newsletter successfully!"
            alert = "success"
            mark = "check"
            return JsonResponse({"succes": True, "data": value, "message":message, "alert":alert,"mark":mark,}, safe=False)
        else:
            message="The email is already subscribed."
            alert = "danger"
            mark = "cross"
            return JsonResponse({"success": True, "data": value, "message":message,"alert":alert, "mark":mark,}, safe=False)

    return JsonResponse({"success": False, "data": None, }, safe=False)