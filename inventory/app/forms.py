from django.forms import ModelForm
from .models import Item, Incident

class ItemForm(ModelForm):
    class Meta:
        model = Item 
        fields = "__all__"

class IncidentForm(ModelForm):
    class Meta:
        model = Incident
        fields = "__all__"
        exclude = ['requester']