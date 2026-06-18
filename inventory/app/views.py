from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Item, Incident, Comment, Software, Asset
from .forms import ItemForm, IncidentForm, CommentForm, UserUpdateForm, ProfileUpdateForm, CustomUserCreationForm, SoftwareForm, AssetForm
from django.contrib.admin.views.decorators import staff_member_required
import random
import string
from django.db.models import F, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

@login_required(login_url='login')
def dashboard(request):
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(qty__lte=F('min_qty')).count()
    low_stock_items_list = Item.objects.filter(qty__lte=F('min_qty'))[:5]
    total_incidents = Incident.objects.count()
    open_incidents = Incident.objects.filter(status='Open').count()
    recent_incidents = Incident.objects.all().order_by('-created')[:5]
    software_data = Software.objects.all()
    
    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'low_stock_items_list': low_stock_items_list,
        'total_incidents': total_incidents,
        'open_incidents': open_incidents,
        'recent_incidents': recent_incidents,
        'software_data': software_data,
    }
    return render(request, 'app/dashboard.html', context)


@login_required(login_url='login')
def inventory(request):  # Rename from home to inventory
    search_query = request.GET.get('search', '')
    items = Item.objects.all()
    
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    context = {
        'items': items,
        'search_query': search_query
    }
    return render(request, 'app/inventory.html', context)


@login_required(login_url='login')
def incidentPage(request):
    search_query = request.GET.get('search', '')
    days = request.GET.get('days', '')
    status_filter = request.GET.get('status', 'active')  # Default to active incidents
    
    incidents = Incident.objects.all()
    
    # Filter by search query
    if search_query:
        incidents = incidents.filter(
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by days
    if days:
        cutoff_date = timezone.now() - timedelta(days=int(days))
        incidents = incidents.filter(created__gte=cutoff_date)
    
    # Filter by status
    if status_filter == 'active':
        incidents = incidents.exclude(status__in=['R', 'C'])
    elif status_filter != 'all':
        incidents = incidents.filter(status=status_filter)
    
    context = {
        'incidents': incidents,
        'search_query': search_query,
        'days': days,
        'status_filter': status_filter,
    }
    return render(request, 'app/incidents/incidents.html', context)


@login_required(login_url='login')
def incident(request, pk):
    incident = Incident.objects.get(id=pk)
    comments = incident.comments.all()
    comment_form = CommentForm()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.incident = incident
            comment.author = request.user
            comment.save()
            return redirect('incident', pk=pk)

    context = {
        'incident': incident,
        'comments': comments,
        'comment_form': comment_form
    }
    return render(request, 'app/incidents/incident.html', context)


@login_required(login_url='login')
def createIncident(request):

    if request.method == 'POST':
        form = IncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.requester = request.user
            incident.save()
            return redirect('incidents')
    else:
        form = IncidentForm()
    
    context = {'form': form}
    return render(request, 'app/incidents/create_incident.html', context)


@login_required(login_url='login')
def editIncident(request, pk):
    incident = Incident.objects.get(id=pk)

    if request.user != incident.requester:
        messages.error(request, 'You are not authorized to edit this incident.')
        return redirect('incident', pk=pk)
        
    form = IncidentForm(instance=incident)

    if request.method == 'POST':
        form = IncidentForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            return redirect('incident', pk=pk)

    context = {'incident': incident, 'form': form}
    return render(request, 'app/incidents/edit_incident.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Incorrect username or password, please try again.')
    return render(request, 'app/login.html')


@login_required(login_url='login')
@require_POST
def logoutUser(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def createItem(request):
    form = ItemForm()

    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.updated_by = request.user
            item.save()
            return redirect('inventory')
    
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
            return redirect('inventory')

    context = {'form': form}
    return render(request, 'app/edit_item.html', context)


@login_required(login_url='login')
def deleteItem(request, pk):
    item = Item.objects.get(id=pk)

    if request.method == 'POST':
        item.delete()
        return redirect('inventory')
    return render(request, 'app/delete_item.html', {'obj':item})


@login_required(login_url='login')
def add_comment(request, pk):
    incident = Incident.objects.get(id=pk)
    if request.method == 'POST':
        content = request.POST.get('content')
        comment = Comment.objects.create(
            incident=incident,
            author=request.user,
            content=content
        )
        return redirect('incident', pk=pk)
    return redirect('incident', pk=pk)


@login_required(login_url='login')
def delete_comment(request, pk, comment_id):
    comment = Comment.objects.get(id=comment_id)
    incident_id = comment.incident.id
    
    if request.user != comment.author:
        messages.error(request, 'You are not authorized to delete this comment.')
        return redirect('incident', pk=incident_id)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
        return redirect('incident', pk=incident_id)
    return redirect('incident', pk=incident_id)


@login_required(login_url='login')
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'app/users/profile.html', context)

@login_required(login_url='login')
@staff_member_required
def users_list(request):
    users = User.objects.all()
    context = {'users': users}
    return render(request, 'app/users/users_list.html', context)


@login_required(login_url='login')
@staff_member_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('users')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'app/users/create_user.html', {'form': form})

@login_required(login_url='login')
def asset_list(request):
    search_query = request.GET.get('search', '')
    assets = Asset.objects.all()
    
    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(tag__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    context = {
        'assets': assets,
        'search_query': search_query
    }
    return render(request, 'app/assets/asset_list.html', context)

@login_required(login_url='login')
def create_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assets')
    else:
        form = AssetForm()
    
    context = {'form': form}
    return render(request, 'app/assets/create_asset.html', context)

@login_required(login_url='login')
def delete_asset(request, pk):
    asset = Asset.objects.get(id=pk)
    if request.method == 'POST':
        asset.delete()
        return redirect('assets')
    return render(request, 'app/assets/delete_asset.html', {'obj': asset})

@login_required(login_url='login')
def edit_asset(request, id):
    asset = Asset.objects.get(id=id)
    form = AssetForm(instance=asset)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('assets')
    context = {'form': form}
    return render(request, 'app/assets/edit_asset.html', context)

@login_required(login_url='login')
def software_list(request):
    search_query = request.GET.get('search', '')
    software_list = Software.objects.all()
    
    if search_query:
        software_list = software_list.filter(
            Q(name__icontains=search_query) |
            Q(version__icontains=search_query) |
            Q(software_license__icontains=search_query)
        )
    
    context = {
        'software_list': software_list,
        'search_query': search_query
    }
    return render(request, 'app/software/software_list.html', context)


@login_required(login_url='login')
def create_software(request):
    if request.method == 'POST':
        form = SoftwareForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('software-list')
    else:
        form = SoftwareForm()
    
    context = {'form': form}
    return render(request, 'app/software/create_software.html', context)


@login_required(login_url='login')
def delete_software(request, pk):
    software = Software.objects.get(id=pk)
    if request.method == 'POST':
        software.delete()
        return redirect('software-list')
    return render(request, 'app/software/delete_software.html', {'obj': software})


@login_required(login_url='login')
def software_detail(request, pk):
    software = get_object_or_404(Software, pk=pk)
    all_users = User.objects.all()
    if request.method == 'POST':
        form = SoftwareForm(request.POST, instance=software)
        if form.is_valid():
            form.save()
            return redirect('software-detail', pk=pk)
    else:
        form = SoftwareForm(instance=software)
    
    context = {
        'software': software,
        'form': form,
        'all_users': all_users
    }
    return render(request, 'app/software/software_page.html', context)

@require_POST
@login_required(login_url='login')
def assign_user(request, pk):
    software = get_object_or_404(Software, pk=pk)
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, id=user_id)
    software.users.add(user)
    return JsonResponse({
        'success': True,
        'user': {
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name()
        }
    })
