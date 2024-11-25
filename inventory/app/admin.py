from django.contrib import admin
from .models import Item, Incident, Comment, Software

# Register your models here.
admin.site.register(Item)
admin.site.register(Incident)
admin.site.register(Comment)
admin.site.register(Software)