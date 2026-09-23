from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(allowed_roles):
    """Decorator to restrict views based on user role."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login first.')
                return redirect('login')

            # Superuser = Admin
            if 'Admin' in allowed_roles and request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Staff = Manager
            if 'Manager' in allowed_roles and request.user.is_staff:
                return view_func(request, *args, **kwargs)

            # Salesman = regular user
            if 'Salesman' in allowed_roles and not request.user.is_staff and not request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return wrapper
    return decorator