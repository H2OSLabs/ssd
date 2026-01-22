from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """
    Display list of notifications for the current user.
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    unread_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications[:50],  # Limit to most recent 50
        'unread_count': unread_count,
    }

    return render(request, 'notifications/notification_list.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """
    Mark a single notification as read.
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    notification.mark_as_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_read(request):
    """
    Mark all notifications as read for the current user.
    """
    from django.utils import timezone

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('notifications:list')
