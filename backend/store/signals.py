from .models import Customer
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
'''
Ham har user ke create hone ke bad user create hamain signal send karta
phir ham us signal ko sunte hain or true hone par
new customer us user ke name se bna dete hain
Signals diferrent taarike ke hote hain
Signals file ko apps.py file main add karna lazmi ha
'''
@receiver(post_save,sender = settings.AUTH_USER_MODEL)
def create_customer_for_each_user(sender,**kwargs):
    if kwargs['created']:
        Customer.objects.create(user=kwargs['instance'])