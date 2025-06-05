# usermanagement/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from tenancy.models import Tenant
import uuid
from django.conf import settings
# class CustomUser(AbstractUser):
#     full_name = models.CharField(max_length=100)
#     role = models.CharField(max_length=50, choices=[("superadmin", "Super Admin"), ("admin", "Admin"), ("user", "User")])
#     company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, blank=True)

#     def __str__(self):
#         return self.username
    

class Organization(models.Model):
    parent_organization = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    legal_name = models.CharField(max_length=200, null=True, blank=True)
    tax_id = models.CharField(max_length=50, null=True, blank=True)
    registration_number = models.CharField(max_length=50, null=True, blank=True)
    industry_code = models.CharField(max_length=20, null=True, blank=True)
    fiscal_year_start_month = models.SmallIntegerField(default=1)
    fiscal_year_start_day = models.SmallIntegerField(default=1)
    base_currency_code = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, default="active")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    
class OrganizationAddress(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=50)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(max_length=2)
    is_primary = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class OrganizationContact(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class CustomUser(AbstractUser):
    user_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=[("superadmin", "Super Admin"), ("admin", "Admin"), ("user", "User")])
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)

    # New fields from schema
    status = models.CharField(max_length=20, default='active')
    auth_provider = models.CharField(max_length=50, default='local')
    auth_provider_id = models.CharField(max_length=255, null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.SmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    mfa_type = models.CharField(max_length=20, null=True, blank=True)
    mfa_secret = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
    
    def organizations(self):
        return self.userorganization_set.all()

    def get_active_organization(self):
        return self.organizations().first()  # or session-based logic

# class Company(models.Model):
#     name = models.CharField(max_length=255)
#     domain = models.CharField(max_length=255, unique=True)

#     def __str__(self):
#         return self.name


class UserOrganization(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    role = models.CharField(max_length=50, default='member')
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')
        db_table = 'user_organizations'

    def __str__(self):
        return f"{self.user.username} - {self.organization.name}"

class Module(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Entity(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='entities')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.module.name} - {self.name}"


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('usermanagement.CustomUser', on_delete=models.CASCADE, related_name='created_by')
    updated_by = models.ForeignKey('usermanagement.CustomUser', on_delete=models.CASCADE, related_name='updated_by')

    class Meta:
        abstract = True
class LoginLog(models.Model):
    login_datetime = models.DateTimeField(auto_now_add=True)
    # user = models.ForeignKey('usermanagement.CustomUser', on_delete=models.CASCADE)
    user = models.ForeignKey('usermanagement.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    # user = models.ForeignKey('usermanagement.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    login_method = models.CharField(max_length=50, choices=[("email", "Email"), ("google", "Google"), ("facebook", "Facebook")])
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    session_time = models.DurationField(null=True, blank=True)
    session_id =  models.CharField(max_length=64, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('usermanagement.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_logs')
    # created_by = models.ForeignKey('usermanagement.CustomUser', on_delete=models.CASCADE,  null=True, blank=True,related_name='created_by')
    
    def is_password_expired(self):
        return (timezone.now() - self.password_changed_at) > timezone.timedelta(days=90)
    def __str__(self):
        return f"{self.user.username} - {self.login_datetime}"
