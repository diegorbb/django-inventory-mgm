from django.db import models


class Item(models.Model):
    # Name, Description, Location, Minimum Qty, Qty, Last Updated, Updated By, 
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=50)
    min_qty = models.PositiveIntegerField(null=True, blank=True)
    qty = models.PositiveIntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    # updated_by = 

    def __str__(self):
        return self.name
    
    
