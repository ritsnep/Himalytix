from usermanagement.models import EntityPermission, Entity, Module

def permissions(request):
    """Add user permissions to template context."""
    if not request.user.is_authenticated:
        return {'user_permissions': {}}

    # Get all permissions for the user's roles
    permissions = EntityPermission.objects.filter(
        role__user_roles__user=request.user,
        is_active=True
    ).select_related('entity')

    # Create a dictionary of permissions
    user_permissions = {}
    for perm in permissions:
        if perm.entity.code not in user_permissions:
            user_permissions[perm.entity.code] = set()
        user_permissions[perm.entity.code].add(perm.action)

    return {
        'user_permissions': user_permissions,
        'has_permission': lambda entity_code, action: (
            entity_code in user_permissions and 
            action in user_permissions[entity_code]
        )
    }

def menu(request):
    """Add menu items to template context."""
    if not request.user.is_authenticated:
        return {'menu_items': []}

    # Get all modules with their entities
    modules = Module.objects.filter(
        is_active=True
    ).prefetch_related(
        'entities'
    ).order_by('order')

    menu_items = []
    for module in modules:
        # Get entities for this module that the user has permission to view
        entities = Entity.objects.filter(
            module=module,
            is_active=True,
            entity_permissions__role__user_roles__user=request.user,
            entity_permissions__action='view',
            entity_permissions__is_active=True
        ).distinct()

        if entities.exists():
            menu_items.append({
                'name': module.name,
                'code': module.code,
                'icon': module.icon,
                'entities': [
                    {
                        'name': entity.name,
                        'code': entity.code,
                        'url': entity.url_pattern,
                        'permissions': {
                            'view': True,
                            'create': EntityPermission.objects.filter(
                                role__user_roles__user=request.user,
                                entity=entity,
                                action='create',
                                is_active=True
                            ).exists(),
                            'edit': EntityPermission.objects.filter(
                                role__user_roles__user=request.user,
                                entity=entity,
                                action='edit',
                                is_active=True
                            ).exists(),
                            'delete': EntityPermission.objects.filter(
                                role__user_roles__user=request.user,
                                entity=entity,
                                action='delete',
                                is_active=True
                            ).exists(),
                        }
                    }
                    for entity in entities
                ]
            })

    return {'menu_items': menu_items} 