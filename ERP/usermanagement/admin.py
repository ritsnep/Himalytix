from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Module, Entity,
    Organization, OrganizationAddress, OrganizationContact
)

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
