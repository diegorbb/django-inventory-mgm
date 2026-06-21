from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Item, Incident, IncidentActivity, Comment, Software, Asset
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
@login_required(login_url='login')
def incidentPage(request):
    search_query = request.GET.get('search', '')
    days = request.GET.get('days', '')
    status_filter = request.GET.get('status', 'active')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    assignee_filter = request.GET.get('assignee', '')

    incidents = Incident.objects.select_related('requester', 'assigned_to').all()

    if search_query:
        incidents = incidents.filter(
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requester__username__icontains=search_query)
        )
    if days:
        cutoff = timezone.now() - timedelta(days=int(days))
        incidents = incidents.filter(created__gte=cutoff)
    if status_filter == 'active':
        incidents = incidents.exclude(status__in=['R', 'C'])
    elif status_filter == 'mine':
        incidents = incidents.filter(assigned_to=request.user).exclude(status__in=['R', 'C'])
    elif status_filter == 'unassigned':
        incidents = incidents.filter(assigned_to__isnull=True).exclude(status__in=['R', 'C'])
    elif status_filter != 'all':
        incidents = incidents.filter(status=status_filter)
    if priority_filter:
        incidents = incidents.filter(priority=priority_filter)
    if category_filter:
        incidents = incidents.filter(category=category_filter)
    if assignee_filter:
        incidents = incidents.filter(assigned_to__id=assignee_filter)

    # Stats for the list header
    all_active = Incident.objects.exclude(status__in=['R', 'C'])
    stats = {
        'open': all_active.filter(status='O').count(),
        'pending': all_active.filter(status='P').count(),
        'urgent': all_active.filter(priority='U').count(),
        'unassigned': all_active.filter(assigned_to__isnull=True).count(),
        'mine': all_active.filter(assigned_to=request.user).count(),
    }
    agents = User.objects.filter(is_staff=True).order_by('username')

    context = {
        'incidents': incidents,
        'search_query': search_query,
        'days': days,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'assignee_filter': assignee_filter,
        'stats': stats,
        'agents': agents,
        'categories': Incident.CATEGORY_CHOICES,
    }
    return render(request, 'app/incidents/incidents.html', context)


@login_required(login_url='login')
def incident(request, pk):
    inc = get_object_or_404(Incident, id=pk)
    comments = inc.comments.all()
    activity = inc.activity.select_related('user').all()
    agents = User.objects.filter(is_staff=True).order_by('username')
    comment_form = CommentForm()
    context = {
        'incident': inc,
        'comments': comments,
        'activity': activity,
        'comment_form': comment_form,
        'agents': agents,
        'priorities': Incident.PRIORITY_CHOICES,
        'statuses': Incident.STATUS_CHOICES,
        'categories': Incident.CATEGORY_CHOICES,
    }
    return render(request, 'app/incidents/incident.html', context)


@login_required(login_url='login')
def createIncident(request):
    agents = User.objects.filter(is_staff=True).order_by('username')
    if request.method == 'POST':
        form = IncidentForm(request.POST)
        if form.is_valid():
            inc = form.save(commit=False)
            inc.requester = request.user
            inc.save()
            IncidentActivity.objects.create(
                incident=inc, user=request.user, action='created',
                detail=f'Incident created by {request.user.username}'
            )
            _notify_assignment(inc, request)
            messages.success(request, f'Incident #{inc.id} created.')
            return redirect('incident', pk=inc.id)
    else:
        form = IncidentForm()
    return render(request, 'app/incidents/create_incident.html', {'form': form, 'agents': agents, 'categories': Incident.CATEGORY_CHOICES})


@login_required(login_url='login')
def editIncident(request, pk):
    inc = get_object_or_404(Incident, id=pk)
    agents = User.objects.filter(is_staff=True).order_by('username')
    if request.method == 'POST':
        old_status = inc.status
        old_priority = inc.priority
        old_assigned = inc.assigned_to_id
        form = IncidentForm(request.POST, instance=inc)
        if form.is_valid():
            updated = form.save(commit=False)
            # Track resolution time
            if updated.status in ('R', 'C') and not inc.resolved_at:
                updated.resolved_at = timezone.now()
            elif updated.status in ('O', 'P') and inc.resolved_at:
                updated.resolved_at = None
            updated.save()
            # Log activities
            if updated.status != old_status:
                IncidentActivity.objects.create(
                    incident=updated, user=request.user, action='status',
                    detail=f'{dict(Incident.STATUS_CHOICES).get(old_status)} → {dict(Incident.STATUS_CHOICES).get(updated.status)}'
                )
                if updated.status in ('R', 'C'):
                    IncidentActivity.objects.create(incident=updated, user=request.user, action='resolved', detail='')
            if updated.priority != old_priority:
                IncidentActivity.objects.create(
                    incident=updated, user=request.user, action='priority',
                    detail=f'{dict(Incident.PRIORITY_CHOICES).get(old_priority)} → {dict(Incident.PRIORITY_CHOICES).get(updated.priority)}'
                )
            if updated.assigned_to_id != old_assigned:
                name = updated.assigned_to.username if updated.assigned_to else 'Unassigned'
                IncidentActivity.objects.create(
                    incident=updated, user=request.user, action='assigned',
                    detail=f'Assigned to {name}'
                )
                _notify_assignment(updated, request)
            messages.success(request, 'Incident updated.')
            return redirect('incident', pk=pk)
    else:
        form = IncidentForm(instance=inc)
    context = {'incident': inc, 'form': form, 'agents': agents, 'categories': Incident.CATEGORY_CHOICES}
    return render(request, 'app/incidents/edit_incident.html', context)


@login_required(login_url='login')
@require_POST
def incident_quick_update(request, pk):
    """AJAX endpoint for inline status/priority/assignee changes from detail page."""
    inc = get_object_or_404(Incident, id=pk)
    data = json.loads(request.body)
    field = data.get('field')
    value = data.get('value')
    allowed = {'status', 'priority', 'assigned_to'}
    if field not in allowed:
        return JsonResponse({'success': False, 'error': 'Invalid field'})

    old_val = getattr(inc, field + '_id' if field == 'assigned_to' else field)

    if field == 'assigned_to':
        inc.assigned_to = User.objects.filter(id=value).first() if value else None
        name = inc.assigned_to.username if inc.assigned_to else 'Unassigned'
        IncidentActivity.objects.create(incident=inc, user=request.user, action='assigned', detail=f'Assigned to {name}')
        _notify_assignment(inc, request)
    elif field == 'status':
        old_status = inc.status
        inc.status = value
        if value in ('R', 'C') and not inc.resolved_at:
            inc.resolved_at = timezone.now()
        elif value in ('O', 'P'):
            inc.resolved_at = None
        IncidentActivity.objects.create(
            incident=inc, user=request.user, action='status',
            detail=f'{dict(Incident.STATUS_CHOICES).get(old_status)} → {dict(Incident.STATUS_CHOICES).get(value)}'
        )
    elif field == 'priority':
        old_priority = inc.priority
        inc.priority = value
        IncidentActivity.objects.create(
            incident=inc, user=request.user, action='priority',
            detail=f'{dict(Incident.PRIORITY_CHOICES).get(old_priority)} → {dict(Incident.PRIORITY_CHOICES).get(value)}'
        )
    inc.save()
    return JsonResponse({'success': True})


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
@require_POST
def add_comment(request, pk):
    inc = get_object_or_404(Incident, id=pk)
    content = request.POST.get('content', '').strip()
    is_internal = request.POST.get('is_internal') == 'on'
    if content:
        Comment.objects.create(
            incident=inc,
            author=request.user,
            content=content,
            is_internal=is_internal
        )
        IncidentActivity.objects.create(
            incident=inc, user=request.user, action='comment',
            detail='Internal note' if is_internal else 'Public reply'
        )
        _notify_comment(inc, request.user, content, is_internal)
    return redirect('incident', pk=pk)


@login_required(login_url='login')
@require_POST
def delete_comment(request, pk, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
    return redirect('incident', pk=pk)


def _notify_assignment(incident, request):
    """Stub: send email to assigned agent. Wire up SMTP in settings to activate."""
    if not incident.assigned_to or not incident.assigned_to.email:
        return
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        if not getattr(settings, 'EMAIL_HOST', None):
            return
        send_mail(
            subject=f'[Incident #{incident.id}] Assigned to you: {incident.subject}',
            message=(
                f'You have been assigned incident #{incident.id}.\n\n'
                f'Subject: {incident.subject}\n'
                f'Priority: {incident.get_priority_display()}\n'
                f'Category: {incident.get_category_display()}\n\n'
                f'View it at: {request.build_absolute_uri(f"/incident/{incident.id}/")}\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[incident.assigned_to.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _notify_comment(incident, author, content, is_internal):
    """Stub: notify requester on public reply. Wire up SMTP in settings to activate."""
    if is_internal:
        return
    if not incident.requester or not incident.requester.email:
        return
    if incident.requester == author:
        return
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        if not getattr(settings, 'EMAIL_HOST', None):
            return
        send_mail(
            subject=f'[Incident #{incident.id}] New reply: {incident.subject}',
            message=(
                f'{author.username} replied to your incident.\n\n'
                f'{content[:500]}\n\n'
                f'View the full thread at: /incident/{incident.id}/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[incident.requester.email],
            fail_silently=True,
        )
    except Exception:
        pass


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
@login_required(login_url='login')
@staff_member_required
def users_list(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('username')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    if role_filter == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif role_filter == 'admin':
        users = users.filter(is_superuser=True)
    elif role_filter == 'user':
        users = users.filter(is_staff=False, is_superuser=False)
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'total': User.objects.count(),
        'active': User.objects.filter(is_active=True).count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
    }
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
@staff_member_required
def edit_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    # Prevent non-superusers from editing superusers
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Only admins can edit other admins.')
        return redirect('users')
    if request.method == 'POST':
        target.first_name = request.POST.get('first_name', '').strip()
        target.last_name  = request.POST.get('last_name', '').strip()
        target.email      = request.POST.get('email', '').strip()
        # Only superusers can change staff/admin flags
        if request.user.is_superuser:
            target.is_staff     = request.POST.get('is_staff') == 'on'
            target.is_superuser = request.POST.get('is_superuser') == 'on'
            if target.is_superuser:
                target.is_staff = True
        new_pw = request.POST.get('new_password', '').strip()
        if new_pw:
            target.set_password(new_pw)
        target.save()
        messages.success(request, f'{target.username} updated.')
        return redirect('users')
    context = {'target': target}
    return render(request, 'app/users/edit_user.html', context)


@login_required(login_url='login')
@staff_member_required
def delete_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('users')
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Only admins can delete other admins.')
        return redirect('users')
    if request.method == 'POST':
        username = target.username
        target.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('users')
    return render(request, 'app/users/delete_user.html', {'target': target})


@login_required(login_url='login')
@staff_member_required
@require_POST
def toggle_user_status(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return JsonResponse({'success': False, 'error': 'Cannot deactivate yourself'})
    if target.is_superuser and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Only admins can change admin status'})
    target.is_active = not target.is_active
    target.save()
    return JsonResponse({'success': True, 'is_active': target.is_active})


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
