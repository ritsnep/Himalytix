from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.apps import apps
from .models import (
    CustomUser, Module, Entity,
    Organization, OrganizationAddress, OrganizationContact,
    Permission, Role, UserOrganization, UserRole
)
@admin.register(UserOrganization)
class UserOrganizationAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'is_owner', 'is_active', 'role', 'date_joined')
    list_filter = ('is_owner', 'is_active', 'role')
    search_fields = ('user__username', 'organization__name')
    readonly_fields = ('date_joined',)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'username', 'email', 'full_name', 'role', 'organization', 'is_active',
        'auth_provider', 'mfa_enabled', 'last_login_at'
    )
    fieldsets = UserAdmin.fieldsets + (
        ("Extended Info", {
            'fields': (
                'full_name', 'role', 'organization',
                'status', 'auth_provider', 'auth_provider_id',
                'last_login_at', 'password_changed_at',
                'password_reset_token', 'password_reset_expires',
                'failed_login_attempts', 'locked_until',
                'email_verified_at', 'email_verification_token',
                'mfa_enabled', 'mfa_type', 'mfa_secret',
                'created_at', 'updated_at', 'deleted_at',
            )
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

# Organization Models
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'legal_name', 'status', 'is_active')
    search_fields = ('name', 'code', 'legal_name')


@admin.register(OrganizationAddress)
class OrganizationAddressAdmin(admin.ModelAdmin):
    list_display = ('organization', 'address_type', 'city', 'country_code', 'is_primary')
    search_fields = ('organization__name', 'city')


@admin.register(OrganizationContact)
class OrganizationContactAdmin(admin.ModelAdmin):
    list_display = ('organization', 'name', 'email', 'contact_type', 'is_primary')
    search_fields = ('organization__name', 'name', 'email')

# Module and Entity
admin.site.register(Module)
admin.site.register(Entity)

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'module', 'entity', 'action')
    list_filter = ('module', 'entity', 'action')
    search_fields = ('name', 'codename')
    readonly_fields = ('codename',)

    def get_queryset(self, request):
        # Only show permissions to superadmin
        if request.user.role != 'superadmin':
            return Permission.objects.none()
        return super().get_queryset(request)

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_system')
    list_filter = ('organization', 'is_system')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

    def get_queryset(self, request):
        # Only show roles to superadmin
        if request.user.role != 'superadmin':
            return Role.objects.none()
        return super().get_queryset(request)

class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('user__username', 'role__name')

    def get_queryset(self, request):
        # Only show user roles to superadmin
        if request.user.role != 'superadmin':
            return UserRole.objects.none()
        return super().get_queryset(request)

# Register the admin classes
admin.site.register(Permission, PermissionAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(UserRole, UserRoleAdmin)
