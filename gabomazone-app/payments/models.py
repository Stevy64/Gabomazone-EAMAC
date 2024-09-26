from django.db import models
from django.contrib.auth.models import User
from accounts.models import Profile
from stripe import BankAccount
# Create your models here.
class VendorPayments(models.Model):
    vendor_profile = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    request_amount = models.FloatField(default=0.00, blank=True, null=True)
    fee = models.FloatField(default=0.00, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    Paid = 'Paid'
    Pending = 'Pending'
    Progressing = 'Progressing'
    Refunded = 'Refunded'
    Status_select = [
        (Paid, 'Paid'),
        (Pending, 'Pending'),
        (Progressing, 'Progressing'),
        (Refunded, 'Refunded'),
    ]
    status = models.CharField(
        max_length=13,
        choices=Status_select,
        default=Pending,
    )

    Bank = 'Bank'
    Paypal = 'Paypal'
    method_select = [
        (Bank, 'Bank'),
        (Paypal, 'Paypal'),
       
    ]
    method = models.CharField(
        max_length=15,
        choices=method_select,
        default=Bank,
    )
    comment = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        ordering = ('-id',)
    # def __str__(self):
    #     return str(self.id)