from django.forms import ModelForm
from .models import Item, Incident, Comment, UserProfile, Software
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class ItemForm(ModelForm):
    class Meta:
        model = Item 
        fields = "__all__"


class IncidentForm(ModelForm):
    class Meta:
        model = Incident
        fields = "__all__"
        exclude = ['requester']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 text-sm text-gray-900 dark:text-white focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Add a comment...',
                'rows': '3'
            })
        }


class SoftwareForm(ModelForm):
    class Meta:
        model = Software
        fields = ['name', 'version', 'software_license', 'license_count']


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