from django.http import HttpResponseForbidden
from usermanagement.utils import PermissionUtils

class UserOrganizationMixin:
    """
    Mixin to provide self.organization = request.user.organization
    and inject it into form kwargs and queryset.
    """
    def get_organization(self):
        user = getattr(self.request, "user", None)
        if user and hasattr(user, "get_active_organization"):
            org = user.get_active_organization()
            if org:
                return org
        return getattr(user, "organization", None)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        org = self.get_organization()
        if org:
            kwargs['organization'] = org
        return kwargs

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.get_organization()
        if org and hasattr(qs.model, "organization_id"):
            return qs.filter(organization=org)
        return qs

class PermissionRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'permission_required'):
            return super().dispatch(request, *args, **kwargs)
        module, entity, action = self.permission_required
        if not PermissionUtils.has_permission(request.user, request.user.organization, module, entity, action):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
