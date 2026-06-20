from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

def default_warranty_date():
    return timezone.now() + timezone.timedelta(days=365)


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


class Asset(models.Model):
    name = models.CharField(max_length=200)
    tag = models.CharField(max_length=50)
    model = models.CharField(max_length=50, default=None)
    hardware = models.CharField(max_length=50, default=None)
    serial = models.CharField(max_length=50, default=None)
    purchase_date = models.DateField(default=timezone.now)
    warranty = models.DateField(default=default_warranty_date) 
    status = models.CharField(max_length=10, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

    
    
class Incident(models.Model):
    STATUS_CHOICES = (
        ("O", "Open"),
        ("P", "Pending"),
        ("C", "Closed"),
        ("R", "Resolved"),
        ("NA", "NA"),
    )

    PRIORITY_CHOICES = (
        ("L", "Low"),
        ("M", "Medium"),
        ("H", "High"),
        ("U", "Urgent"),
    )

    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subject = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='O')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='L')
    description = models.TextField()
    created = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.subject
    

class Comment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    content_html = models.TextField(editable=False, null=True, blank=True)  # Make nullable
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.author.username} - {self.created.strftime("%Y-%m-%d %H:%M")}'

    def save(self, *args, **kwargs):
        import markdown
        self.content_html = markdown.markdown(self.content, extensions=['fenced_code'])
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profile_images', default='default.png')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Software(models.Model):
    LICENSE_TYPE_CHOICES = [
        ('perpetual', 'Perpetual'),
        ('subscription', 'Subscription'),
        ('oem', 'OEM'),
        ('open_source', 'Open Source'),
        ('freeware', 'Freeware'),
    ]

    name = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, blank=True, default='')
    version = models.CharField(max_length=50)
    category = models.CharField(max_length=100, blank=True, default='')
    software_license = models.CharField(max_length=200, blank=True, default='')
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, default='perpetual')
    license_count = models.PositiveIntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    updated = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, related_name='software', blank=True)

    def __str__(self):
        return self.name

    @property
    def seats_used(self):
        return self.users.count()

    @property
    def seats_available(self):
        return self.license_count - self.users.count()

    @property
    def is_over_limit(self):
        return self.users.count() > self.license_count


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()