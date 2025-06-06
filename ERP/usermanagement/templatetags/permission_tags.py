from django import template
from usermanagement.utils import PermissionUtils

register = template.Library()

@register.filter
def has_permission(user, permission_string):
    # Super admin has all permissions
    if user.role == 'superadmin':
        return True
        
    module, entity, action = permission_string.split('_')
    return PermissionUtils.has_permission(
        user,
        user.get_active_organization(),
        module,
        entity,
        action
    )
