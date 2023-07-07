from django.contrib import admin
from .models import InventoryItem, UploadedFile

admin.site.register(InventoryItem)
admin.site.register(UploadedFile)
