from django.contrib import admin
from .models import Item, Incident, Comment

# Register your models here.
admin.site.register(Item)
admin.site.register(Incident)