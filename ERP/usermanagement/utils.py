from django.core.cache import cache
from django.db import connection
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

class PermissionUtils:
    @staticmethod
    def get_user_permissions(user, organization):
        # Super admin has all permissions
        if user.role == 'superadmin':
            return ['*']  # Special marker for all permissions
            
        if not organization:
            return []
            
        cache_key = f'user_permissions_{user.id}_{organization.id}'
        permissions = cache.get(cache_key)
        
        if permissions is None:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT p.codename, p.module_id, p.entity_id, p.action
                    FROM usermanagement_permission p
                    JOIN usermanagement_role_permissions rp ON p.id = rp.permission_id
                    JOIN usermanagement_role r ON rp.role_id = r.id
                    JOIN usermanagement_userrole ur ON r.id = ur.role_id
                    WHERE ur.user_id = %s 
                    AND ur.organization_id = %s 
                    AND ur.is_active = 1
                """, [user.id, organization.id])
                permissions = cursor.fetchall()
                cache.set(cache_key, permissions, 300)  # Cache for 5 minutes
                
        return permissions

    @staticmethod
    def has_permission(user, organization, module, entity, action):
        # Super admin has all permissions
        if user.role == 'superadmin':
            return True
            
        if not organization:
            return False
            
        permissions = PermissionUtils.get_user_permissions(user, organization)
        if permissions == ['*']:  # Handle super admin case
            return True
            
        return any(p[0] == f"{module}_{entity}_{action}" for p in permissions)

def require_permission(module, entity, action):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            organization = request.user.get_active_organization()
            if not organization:
                messages.warning(request, "Please select an active organization to continue.")
                return HttpResponseRedirect(reverse_lazy('select_organization'))
                
            if not PermissionUtils.has_permission(
                request.user, 
                organization,
                module,
                entity,
                action
            ):
                messages.error(request, "You don't have permission to access this page.")
                return HttpResponseRedirect(reverse_lazy('dashboard'))
            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator 