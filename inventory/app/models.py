from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    # Name, Description, Location, Minimum Qty, Qty, Last Updated, Updated By, 
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=50)
    min_qty = models.PositiveIntegerField(null=True, blank=True)
    qty = models.PositiveIntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
    
    
class Incident(models.Model):
    STATUS_CHOICES = (
        ("Open", "O"),
        ("Pending", "P"),
        ("Closed", "C"),
        ("Resolved", "R"),
        ("NA", "NA"),
    )

    PRIORITY_CHOICES = (
        ("Low", "L"),
        ("Medium", "M"),
        ("High", "H"),
        ("Urgent", "U"),
    )

    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subject = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Low')
    description = models.TextField()
    created = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.subject
    
