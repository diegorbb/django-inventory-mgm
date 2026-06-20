from django.forms import ModelForm
from .models import Item, Incident, Comment, UserProfile, Software, Asset
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'location', 'min_qty', 'qty']


class IncidentForm(ModelForm):
    class Meta:
        model = Incident
        fields = ['subject', 'category', 'priority', 'status', 'assigned_to', 'description']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'is_internal']


class SoftwareForm(ModelForm):
    class Meta:
        model = Software
        fields = ['name', 'publisher', 'version', 'category', 'software_license',
                  'license_type', 'license_count', 'expiry_date', 'notes']


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'tag', 'model', 'hardware', 'serial', 'purchase_date', 'warranty', 'status', 'assigned_to', 'location']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'location', 'phone']


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5'}),
            'email': forms.EmailInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5'}),
            'first_name': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5'}),
            'last_name': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5'})
        self.fields['password2'].widget.attrs.update({'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5'})