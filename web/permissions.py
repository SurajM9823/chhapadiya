from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def permission_required(module, action):
    """Decorator to check user permission before accessing a view."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('panel_login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if request.user.has_permission(module, action):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f'You do not have permission to {action} {module}.')
            return redirect('panel_dashboard')
        
        return wrapper
    return decorator


def check_permission(user, module, action):
    """Check if user has permission for a module action."""
    if user.is_superuser:
        return True
    return user.has_permission(module, action)
