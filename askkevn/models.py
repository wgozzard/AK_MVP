from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
import json

class InventoryItem(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE) 
    alcohol_type = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        app_label = 'inventoryitems'

    def __str__(self):
        return f"{self.alcohol_type} - {self.brand}"

class UploadedFile(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'askkevn'

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        inventory_items = []

        with open(self.file.path) as file:
            inventory_items = json.load(file)

        for item in inventory_items:
            InventoryItem.objects.create(owner=self.owner, data=json.dumps(item))

def determine_expertise(user_input):
    # Logic to determine the expertise area based on user input
    # Modify this function according to your requirements
    expertise = 'general'  # Default expertise

    if 'bourbon' in user_input.lower():
        expertise = 'bourbon'
    elif 'whiskey' in user_input.lower():
        expertise = 'whiskey'
    elif 'wine' in user_input.lower():
        expertise = 'wine'
    elif 'beer' in user_input.lower():
        expertise = 'beer'
    elif 'mezcal' in user_input.lower():
        expertise = 'mezcal'
    elif 'tequila' in user_input.lower():
        expertise = 'tequila'
    elif 'rye' in user_input.lower():
        expertise = 'rye'
    elif 'scotch' in user_input.lower():
        expertise = 'scotch'

    return expertise