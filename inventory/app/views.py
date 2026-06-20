from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Item, Incident, Comment, Software, Asset
from .forms import ItemForm, IncidentForm, CommentForm, UserUpdateForm, ProfileUpdateForm, CustomUserCreationForm, SoftwareForm, AssetForm
from django.contrib.admin.views.decorators import staff_member_required
import json
import random
import string
from django.db.models import F, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

@login_required(login_url='login')
@login_required(login_url='login')
def dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = timezone.now() - timedelta(days=30)
    seven_days_ago = timezone.now() - timedelta(days=7)

    # --- Incidents ---
    all_incidents = Incident.objects.all()
    open_incidents = all_incidents.filter(status='O')
    pending_incidents = all_incidents.filter(status='P')
    urgent_incidents = all_incidents.filter(priority='U', status__in=['O', 'P'])
    resolved_this_month = all_incidents.filter(status__in=['R', 'C'], created__gte=thirty_days_ago.date())
    new_this_week = all_incidents.filter(created__gte=seven_days_ago.date())
    recent_incidents = all_incidents.order_by('-created')[:8]

    # Incident breakdown by priority (open only)
    open_by_priority = {
        'urgent': all_incidents.filter(status__in=['O','P'], priority='U').count(),
        'high':   all_incidents.filter(status__in=['O','P'], priority='H').count(),
        'medium': all_incidents.filter(status__in=['O','P'], priority='M').count(),
        'low':    all_incidents.filter(status__in=['O','P'], priority='L').count(),
    }

    # --- Inventory ---
    total_items = Item.objects.count()
    low_stock_items_list = Item.objects.filter(qty__lte=F('min_qty')).order_by('qty')[:6]
    low_stock_count = Item.objects.filter(qty__lte=F('min_qty')).count()
    out_of_stock_count = Item.objects.filter(qty=0).count()

    # --- Assets ---
    total_assets = Asset.objects.count()
    active_assets = Asset.objects.filter(status='Active').count()
    unassigned_assets = Asset.objects.filter(assigned_to__isnull=True, status='Active').count()
    expiring_warranties = Asset.objects.filter(
        warranty__gte=today,
        warranty__lte=today + timedelta(days=90)
    ).order_by('warranty')[:5]
    expired_warranties = Asset.objects.filter(warranty__lt=today).count()

    # --- Software ---
    all_software = Software.objects.all()
    total_licenses = sum(s.license_count for s in all_software)
    used_licenses = sum(s.seats_used for s in all_software)
    over_limit_software = [s for s in all_software if s.is_over_limit]
    expiring_software = [s for s in all_software
                         if s.expiry_date and today <= s.expiry_date <= today + timedelta(days=90)]
    expired_software = [s for s in all_software
                        if s.expiry_date and s.expiry_date < today]

    # --- Users ---
    total_users = User.objects.filter(is_active=True).count()

    context = {
        'today': today,
        # incidents
        'open_incidents': open_incidents.count(),
        'pending_incidents': pending_incidents.count(),
        'urgent_incidents': urgent_incidents.count(),
        'resolved_this_month': resolved_this_month.count(),
        'new_this_week': new_this_week.count(),
        'recent_incidents': recent_incidents,
        'open_by_priority': open_by_priority,
        # inventory
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'low_stock_items_list': low_stock_items_list,
        # assets
        'total_assets': total_assets,
        'active_assets': active_assets,
        'unassigned_assets': unassigned_assets,
        'expiring_warranties': expiring_warranties,
        'expired_warranties': expired_warranties,
        # software
        'total_licenses': total_licenses,
        'used_licenses': used_licenses,
        'over_limit_software': over_limit_software,
        'expiring_software': expiring_software,
        'expired_software': expired_software,
        # users
        'total_users': total_users,
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
@login_required(login_url='login')
def asset_detail(request, pk):
    asset = Asset.objects.get(id=pk)
    all_users = User.objects.filter(is_active=True).order_by('username')
    context = {'asset': asset, 'all_users': all_users, 'today': timezone.now().date()}
    return render(request, 'app/assets/asset_detail.html', context)



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
@login_required(login_url='login')
def create_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assets')
    else:
        form = AssetForm()
    return render(request, 'app/assets/create_asset.html', {'form': form})


def delete_asset(request, pk):
    asset = Asset.objects.get(id=pk)
    if request.method == 'POST':
        asset.delete()
        return redirect('assets')
    return render(request, 'app/assets/delete_asset.html', {'obj': asset})

@login_required(login_url='login')
@login_required(login_url='login')
def edit_asset(request, id):
    asset = Asset.objects.get(id=id)
    form = AssetForm(instance=asset)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('asset-detail', pk=asset.id)
    context = {'form': form, 'asset': asset}
    return render(request, 'app/assets/edit_asset.html', context)

@login_required(login_url='login')
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
        'search_query': search_query,
        'today': timezone.now().date(),
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
        'all_users': all_users,
        'today': timezone.now().date(),
    }
    return render(request, 'app/software/software_page.html', context)

@require_POST
@login_required(login_url='login')
def assign_user(request, pk):
    software = get_object_or_404(Software, pk=pk)
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
    except Exception:
        user_id = request.POST.get('user_id')
    user = get_object_or_404(User, id=user_id)
    if software.users.filter(id=user.id).exists():
        return JsonResponse({'success': False, 'error': 'User already assigned'})
    software.users.add(user)
    return JsonResponse({
        'success': True,
        'user': {'id': user.id, 'username': user.username, 'email': user.email}
    })


@require_POST
@login_required(login_url='login')
def remove_user(request, pk, user_id):
    software = get_object_or_404(Software, pk=pk)
    user = get_object_or_404(User, id=user_id)
    software.users.remove(user)
    return JsonResponse({'success': True})
