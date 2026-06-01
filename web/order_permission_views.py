from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Role, OrderStatusPermission, Order

@login_required
def manage_order_permissions(request):
    """View to manage order status permissions for all roles."""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('panel_dashboard')
    
    roles = Role.objects.all()
    status_choices = Order.STATUS_CHOICES
    
    # Get existing permissions as a set for easy lookup
    existing_perms = set()
    for perm in OrderStatusPermission.objects.all():
        existing_perms.add(f"{perm.role_id}_{perm.from_status}_{perm.to_status}")
    
    if request.method == 'POST':
        # Clear all existing permissions
        OrderStatusPermission.objects.all().delete()
        
        # Process submitted permissions
        for key, value in request.POST.items():
            if key.startswith('perm_'):
                # Format: perm_roleId_fromStatus_toStatus
                parts = key.split('_')
                if len(parts) == 4:
                    role_id = parts[1]
                    from_status = parts[2]
                    to_status = parts[3]
                    
                    role = Role.objects.get(id=role_id)
                    OrderStatusPermission.objects.create(
                        role=role,
                        from_status=from_status,
                        to_status=to_status
                    )
        
        messages.success(request, 'Order status permissions updated successfully!')
        return redirect('manage_order_permissions')
    
    context = {
        'roles': roles,
        'status_choices': status_choices,
        'existing_perms': existing_perms,
    }
    return render(request, 'panel/order_permissions.html', context)


@login_required
def get_allowed_statuses(request, order_id):
    """API endpoint to get allowed status transitions for current user and order."""
    order = get_object_or_404(Order, id=order_id)
    
    if request.user.is_superuser:
        # Superuser can change to any status
        allowed = [status[0] for status in Order.STATUS_CHOICES]
    elif request.user.role:
        # Get allowed transitions from current status
        allowed = list(
            request.user.role.order_status_permissions
            .filter(from_status=order.status)
            .values_list('to_status', flat=True)
        )
    else:
        allowed = []
    
    return JsonResponse({'allowed_statuses': allowed})
