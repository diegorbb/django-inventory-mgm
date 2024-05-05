from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Item
from .forms import ItemForm

@login_required(login_url='login')
def home(request):

    items = Item.objects.all()

    context = {
        'items': items,
    }

    return render(request, 'app/home.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Incorrect user or password, try again!')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'User does not exist.')
    return render(request, 'app/login.html')


def logoutUser(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def createItem(request):
    form = ItemForm()

    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    
    context = {'form': form}
    return render(request, 'app/create_item.html', context)


@login_required(login_url='login')
def editItem(request, pk):
    item = Item.objects.get(id=pk)
    form = ItemForm(instance=item)

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.instance.updated_by = request.user
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'app/edit_item.html', context)


@login_required(login_url='login')
def deleteItem(request, pk):
    item = Item.objects.get(id=pk)

    if request.method == 'POST':
        item.delete()
        return redirect('home')
    return render(request, 'app/delete_item.html', {'obj':item})