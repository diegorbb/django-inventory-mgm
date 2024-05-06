from django.contrib import admin
from .models import Item, Incident

# Register your models here.
admin.site.register(Item)
admin.site.register(Incident)