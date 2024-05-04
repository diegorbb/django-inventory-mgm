from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Item
from .forms import ItemForm

def home(request):

    items = Item.objects.all()

    context = {
        'items': items,
    }

    return render(request, 'app/home.html', context)


def createItem(request):
    form = ItemForm()

    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    
    context = {'form': form}
    return render(request, 'app/create_item.html', context)


def editItem(request, pk):
    item = Item.objects.get(id=pk)
    form = ItemForm(instance=item)

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'app/edit_item.html', context)
