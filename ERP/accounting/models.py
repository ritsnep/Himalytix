from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from usermanagement.models import CustomUser, Organization
from django.utils.crypto import get_random_string
from django.db.models import Max, Q, F, CheckConstraint
import logging
from django.core.exceptions import ValidationError
from django.db import transaction
logger = logging.getLogger(__name__)

User = get_user_model()


def generate_fiscal_year_id():
    while True:
        id = get_random_string(10, '0123456789')
        if not FiscalYear.objects.filter(fiscal_year_id=id).exists():
            return id
# Example: Fix for AutoIncrementCodeGenerator
class AutoIncrementCodeGenerator:
    def __init__(self, model, field, prefix='', suffix=''):
        self.model = model
        self.field = field
        self.prefix = prefix
        self.suffix = suffix

    def generate_code(self):
        from django.db.models import Max
        import re

        # Find all codes matching the pattern
        pattern = rf'^{re.escape(self.prefix)}(\d+){re.escape(self.suffix)}$'
        codes = self.model.objects.values_list(self.field, flat=True)
        numbers = [
            int(re.match(pattern, code).group(1))
            for code in codes if re.match(pattern, code)
        ]
        next_number = max(numbers, default=0) + 1
        return f"{self.prefix}{str(next_number).zfill(2)}{self.suffix}"
    
class FiscalYear(models.Model):
    """
    Represents a fiscal year for an organization.
    Defines the financial reporting period, status, and audit trail.
    Only one fiscal year per organization can be current at a time.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    id = models.CharField(default=get_random_string(10, '0123456789'), max_length=10, unique=True, editable=False)
    fiscal_year_id = models.CharField(max_length=10,primary_key=True, unique=True, default=generate_fiscal_year_id)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='fiscal_years',
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_current = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_fiscal_years')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_fiscal_years')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_fiscal_years')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_fiscal_years')
    is_default = models.BooleanField(default=False)
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")

    class Meta:
        db_table = 'fiscal_years'
        ordering = ['-start_date']
        unique_together = ('organization', 'code')
        indexes = [
            models.Index(fields=['organization', 'is_current']),
            models.Index(fields=['organization', 'status']),
        ]
        constraints = [
            CheckConstraint(check=Q(start_date__lt=F('end_date')), name='fiscalyear_start_before_end'),
        ]
        # For DBA: Add UNIQUE WHERE is_current=1 and is_default=1 on (organization)
        # For DBA: CLUSTERED INDEX (organization, start_date)
        # For DBA: SYSTEM-VERSIONED TEMPORAL TABLE

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate date order
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

        # Only one is_current per org
        if self.is_current:
            qs = FiscalYear.objects.filter(organization_id=self.organization_id, is_current=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one fiscal year can be current per organization.")

        # Only one is_default per org
        if self.is_default:
            qs = FiscalYear.objects.filter(organization_id=self.organization_id, is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one fiscal year can be default per organization.")

        # Prevent overlapping fiscal years for the same organization
        overlapping = FiscalYear.objects.filter(
            organization_id=self.organization_id,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("Fiscal year dates overlap with another fiscal year for this organization.")

   
        previous = (
            FiscalYear.objects.filter(
                organization_id=self.organization_id,
                end_date__lt=self.start_date,
            )
            .order_by('-end_date')
            .first()
        )
        if previous and (self.start_date - previous.end_date).days != 1:
            raise ValidationError(
                "Fiscal year must start the day after the previous fiscal year ends."
            )

        next_fy = (
            FiscalYear.objects.filter(
                organization_id=self.organization_id,
                start_date__gt=self.end_date,
            )
            .order_by('start_date')
            .first()
        )
        if next_fy and (next_fy.start_date - self.end_date).days != 1:
            raise ValidationError(
                "Fiscal year must end the day before the next fiscal year starts."
            )
    def save(self, *args, **kwargs):
        logger.info(f"Saving FiscalYear: {self.code}")
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(FiscalYear, 'code', prefix='FY', suffix='')
            self.code = code_generator.generate_code()
        # Enforce only one is_current per org
        if self.is_current:
            FiscalYear.objects.filter(organization_id=self.organization_id, is_current=True).exclude(pk=self.pk).update(is_current=False)
        # Enforce only one is_default per org
        if self.is_default:
            FiscalYear.objects.filter(organization_id=self.organization_id, is_default=True).exclude(pk=self.pk).update(is_default=False)
        self.full_clean()
        super(FiscalYear, self).save(*args, **kwargs)

        

class AccountingPeriod(models.Model):
    """
    Represents a period (month, quarter, etc.) within a fiscal year.
    Used for period-based reporting and posting control.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('adjustment', 'Adjustment'),
    ]

    period_id = models.BigAutoField(primary_key=True)
    fiscal_year = models.ForeignKey('FiscalYear', on_delete=models.PROTECT, related_name='periods')
    period_number = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(16)])
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_adjustment_period = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_periods')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_periods')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_periods')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        unique_together = ('fiscal_year', 'period_number')
        ordering = ['fiscal_year', 'period_number']
        constraints = [
            CheckConstraint(check=Q(start_date__lt=F('end_date')), name='period_start_before_end'),
        ]
        # For DBA: UNIQUE (fiscal_year_id, period_number)
        # For DBA: FILTERED INDEX WHERE status='open'
        # For DBA: CHECK start/end inside parent FY
        # For DBA: ROWVERSION

    def __str__(self):
        return f"{self.fiscal_year.name} - {self.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

class Department(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")

    def __str__(self):
        # This will make Department objects display their name in dropdowns and elsewhere
        return self.name 

    class Meta:
        ordering = ['name']
        constraints = [
            CheckConstraint(check=Q(start_date__lt=F('end_date')), name='department_start_before_end'),
        ]
        # For DBA: NONCLUSTERED UNIQUE (organization_id, code)
        # For DBA: FILTERED INDEX WHERE is_active=1

class Project(models.Model):
    project_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        ordering = ['name']
        constraints = [
            CheckConstraint(check=Q(start_date__lt=F('end_date')), name='project_start_before_end'),
        ]
        # For DBA: NONCLUSTERED UNIQUE (organization_id, code)
        # For DBA: FILTERED INDEX WHERE is_active=1
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    def save(self, *args, **kwargs):
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(Project, 'code', prefix='PRJ', suffix='')
            self.code = code_generator.generate_code()
        super(Project, self).save(*args, **kwargs)
class CostCenter(models.Model):
    cost_center_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='cost_centers',null=True, blank=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    class Meta:
        ordering = ['name']
        constraints = [
            CheckConstraint(check=Q(start_date__lt=F('end_date')), name='costcenter_start_before_end'),
        ]
        # For DBA: NONCLUSTERED UNIQUE (organization_id, code)
        # For DBA: FILTERED INDEX WHERE is_active=1
    def __str__(self):
        return f"{self.code} - {self.name}"
    def save(self, *args, **kwargs):
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(CostCenter, 'code', prefix='CC', suffix='')
            self.code = code_generator.generate_code()
        super(CostCenter, self).save(*args, **kwargs)
    # Add other cost center fields as needed

class AccountType(models.Model):
    NATURE_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    NATURE_CODE_PREFIX = {
        'asset': 'AST',
        'liability': 'LIA',
        'equity': 'EQT',
        'income': 'INC',
        'expense': 'EXP',
    }
    account_type_id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES)
    classification = models.CharField(max_length=50)
    balance_sheet_category = models.CharField(max_length=50, null=True, blank=True)
    income_statement_category = models.CharField(max_length=50, null=True, blank=True)
    cash_flow_category = models.CharField(max_length=50, null=True, blank=True)
    system_type = models.BooleanField(default=True)
    display_order = models.BigIntegerField()
    root_code_prefix = models.CharField(max_length=10, null=True, blank=True,
                                        help_text="Starting prefix for top level account codes")
    root_code_step = models.BigIntegerField(default=100,
                                                help_text="Increment step for generating top level codes")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    # Add related_name to fix the reverse accessor conflicts
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_account_types')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_account_types')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_account_types')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    def save(self, *args, **kwargs):
        if not self.root_code_prefix:
            self.root_code_prefix = {
                'asset': '1000',
                'liability': '2000',
                'equity': '3000',
                'income': '4000',
                'expense': '5000',
            }.get(self.nature, '9000')
        if not self.root_code_step:
            self.root_code_step = 100
        if not self.code:
            prefix = self.NATURE_CODE_PREFIX.get(self.nature, 'ACC')
            # Get max code with the same prefix
            max_code = (
                AccountType.objects
                .filter(code__startswith=prefix)
                .aggregate(Max('code'))
                .get('code__max')
            )

            if max_code:
                try:
                    last_num = int(max_code.replace(prefix, ''))
                except ValueError:
                    last_num = 0
            else:
                last_num = 0

            next_num = last_num + 1
            self.code = f"{prefix}{next_num:03d}"  # e.g., AST001

        super(AccountType, self).save(*args, **kwargs)

    class Meta:
        # ... existing meta ...
        constraints = [
            CheckConstraint(check=Q(root_code_step__gt=0), name='accounttype_root_code_step_positive'),
        ]
        # For DBA: PAGE compression, mark as static reference

class Currency(models.Model):
    currency_code = models.CharField(max_length=3, primary_key=True)
    currency_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_currencies')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_currencies')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")

    class Meta:
        verbose_name_plural = "Currencies"
        ordering = ['currency_code']

    def __str__(self):
        return f"{self.currency_code} - {self.currency_name}"



class ChartOfAccount(models.Model):
    # Default starting codes for each account nature. New top level accounts are
    # created using these prefixes and incremented in steps of ``100``.
    # The values also determine the length used when zero padding generated codes.
    NATURE_ROOT_CODE = {
        'asset': '1000',
        'liability': '2000',
        'equity': '3000',
        'income': '4000',
        'expense': '5000',
    }
    ROOT_STEP = 100
    account_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='chart_of_accounts'
    )
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    account_code = models.CharField(max_length=50)
    account_name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_bank_account = models.BooleanField(default=False)
    is_control_account = models.BooleanField(default=False)
    control_account_type = models.CharField(max_length=50, null=True, blank=True)
    require_cost_center = models.BooleanField(default=False)
    require_project = models.BooleanField(default=False)
    require_department = models.BooleanField(default=False)
    default_tax_code = models.CharField(max_length=50, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, null=True, blank=True, related_name='accounts')
    opening_balance = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    current_balance = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    reconciled_balance = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    last_reconciled_date = models.DateTimeField(null=True, blank=True)
    allow_manual_journal = models.BooleanField(default=True)
    account_level = models.SmallIntegerField(default=1)
    tree_path = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_accounts')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_accounts')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_accounts')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        unique_together = ('organization', 'account_code')
        ordering = ['account_code']
        indexes = [
            models.Index(fields=['parent_account']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_active']),
        ]
        # For DBA: Clustered on (organization_id, account_code); non-clustered on parent_account
        # For DBA: tree_path as persisted hierarchyid
        # For DBA: PAGE compression

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"

    def total_balance(self):
        """Return current balance including balances of all child accounts."""
        total = self.current_balance
        for child in ChartOfAccount.objects.filter(parent_account=self):
            total += child.total_balance()
        return total
    def clean(self):
        # Circular reference check
        if self.parent_account:
            ancestor = self.parent_account
            depth = 1
            while ancestor:
                if ancestor == self:
                    raise ValidationError("Circular parent relationship detected.")
                ancestor = ancestor.parent_account
                depth += 1
                if depth > 10:
                    raise ValidationError("Account tree is too deep (max 10 levels).")
        # Suffix overflow check for children
        org_id = getattr(self, 'organization_id', None) or (self.organization.pk if hasattr(self, 'organization') and self.organization else None)
        if self.parent_account:
            if not org_id:
                raise ValidationError("Organization must be set before validating child accounts.")
            siblings = ChartOfAccount.objects.filter(parent_account=self.parent_account, organization_id=org_id)
            if siblings.count() >= 99:
                raise ValidationError("Maximum number of child accounts (99) reached for this parent.")
        super().clean()
    def save(self, *args, **kwargs):
        with transaction.atomic():
            logger.debug(f"ChartOfAccount.save: Called for pk={self.pk}, account_code={self.account_code}")
            if not self.account_code:
                logger.debug("ChartOfAccount.save: Generating account_code...")
                if self.parent_account:
                    siblings = ChartOfAccount.objects.filter(
                        parent_account=self.parent_account,
                        organization=self.organization,
                    )
                    sibling_codes = siblings.values_list('account_code', flat=True)
                    base_code = self.parent_account.account_code
                    used_suffixes = set()
                    for code in sibling_codes:
                        if code.startswith(base_code + "."):
                            try:
                                suffix = int(code.replace(base_code + ".", ""))
                                used_suffixes.add(suffix)
                            except ValueError:
                                continue
                    # Find the first unused suffix from 1 to 99
                    next_suffix = None
                    for i in range(1, 100):
                        if i not in used_suffixes:
                            next_suffix = i
                            break
                    if next_suffix is None:
                        raise ValidationError("Maximum number of child accounts (99) reached for this parent.")
                    self.account_code = f"{base_code}.{next_suffix:02d}"
                    logger.debug(f"ChartOfAccount.save: Generated child account_code={self.account_code}")
                else:
                    root_code = self.account_type and self.account_type.nature
                    root_prefix = (
                        self.account_type.root_code_prefix
                        or self.NATURE_ROOT_CODE.get(root_code, '9000')
                    )
                    step = self.account_type.root_code_step or self.ROOT_STEP
                    top_levels = ChartOfAccount.objects.filter(
                        parent_account__isnull=True,
                        organization=self.organization,
                        account_code__startswith=root_prefix
                    )
                    used_codes = set()
                    for acc in top_levels:
                        try:
                            acc_num = int(acc.account_code)
                            if str(acc_num).startswith(root_prefix):
                                used_codes.add(acc_num)
                        except ValueError:
                            continue
                    # Find the first unused code in the sequence
                    start_code = int(root_prefix)
                    next_code = None
                    for i in range(start_code, start_code + step * 99, step):
                        if i not in used_codes:
                            next_code = i
                            break
                    if next_code is None:
                        raise ValidationError("Maximum number of top-level accounts (99) reached for this type.")
                    self.account_code = str(next_code).zfill(len(root_prefix))
                    logger.debug(f"ChartOfAccount.save: Generated top-level account_code={self.account_code}")
            if self.parent_account:
                self.tree_path = f"{self.parent_account.tree_path}/{self.account_code}" if self.parent_account.tree_path else self.account_code
            else:
                self.tree_path = self.account_code
            self.full_clean()
            logger.debug(f"ChartOfAccount.save: Saving with account_code={self.account_code}")
            super(ChartOfAccount, self).save(*args, **kwargs)
    @classmethod
    def get_next_code(cls, org_id, parent_id, account_type_id):
        from django.db.models import Q
        from django.db import transaction
        if not org_id:
            return None
        with transaction.atomic():
            if parent_id:
                try:
                    parent = cls.objects.get(pk=parent_id)
                except cls.DoesNotExist:
                    return None
                siblings = cls.objects.filter(parent_account=parent, organization_id=org_id)
                sibling_codes = siblings.values_list('account_code', flat=True)
                base_code = parent.account_code
                max_suffix = 0
                for code in sibling_codes:
                    if code.startswith(base_code + "."):
                        try:
                            suffix = int(code.replace(base_code + ".", ""))
                            if suffix > max_suffix:
                                max_suffix = suffix
                        except ValueError:
                            continue
                next_suffix = max_suffix + 1
                if next_suffix > 99:
                    raise ValidationError("Maximum number of child accounts (99) reached for this parent.")
                return f"{base_code}.{next_suffix:02d}"
            else:
                from .models import AccountType
                try:
                    at = AccountType.objects.get(pk=account_type_id)
                except AccountType.DoesNotExist:
                    return None
                root_code = at.nature
                root_prefix = at.root_code_prefix or cls.NATURE_ROOT_CODE.get(root_code, '9000')
                step = at.root_code_step or cls.ROOT_STEP
                top_levels = cls.objects.filter(
                    parent_account__isnull=True,
                    organization_id=org_id,
                    account_code__startswith=root_prefix
                )
                max_code = 0
                for acc in top_levels:
                    try:
                        acc_num = int(acc.account_code)
                        if str(acc_num).startswith(root_prefix) and acc_num > max_code:
                            max_code = acc_num
                    except ValueError:
                        continue
                if max_code >= int(root_prefix):
                    next_code = max_code + step
                else:
                    next_code = int(root_prefix)
                return str(next_code).zfill(len(root_prefix))

class CurrencyExchangeRate(models.Model):
    rate_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='currency_exchange_rates'
    )
    from_currency = models.ForeignKey('Currency', on_delete=models.PROTECT, related_name='exchange_rates_from')
    to_currency = models.ForeignKey('Currency', on_delete=models.PROTECT, related_name='exchange_rates_to')
    rate_date = models.DateField()
    exchange_rate = models.DecimalField(max_digits=19, decimal_places=6)
    is_average_rate = models.BooleanField(default=False)
    source = models.CharField(max_length=50, default='manual')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_exchange_rates')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_exchange_rates')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_exchange_rates')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        unique_together = ('organization', 'from_currency', 'to_currency', 'rate_date')
        ordering = ['-rate_date']
        # For DBA: Composite UNIQUE (org, from, to, rate_date, is_average_rate)
        # For DBA: Clustered index (rate_date DESC, from_currency, to_currency)
        # For DBA: Partition by RANGE RIGHT (rate_date) when rows > 10M

    def __str__(self):
        return f"{self.from_currency.currency_code}/{self.to_currency.currency_code} @ {self.exchange_rate} on {self.rate_date}"


class JournalType(models.Model):
    journal_type_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='journal_types'
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    auto_numbering_prefix = models.CharField(max_length=10, null=True, blank=True)
    auto_numbering_suffix = models.CharField(max_length=10, null=True, blank=True)
    auto_numbering_next = models.BigIntegerField(default=1)
    is_system_type = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_journal_types')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_journal_types')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_journal_types')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        unique_together = ('organization', 'code')
        ordering = ('name',)
        # For DBA: Replace auto_numbering_next with CREATE SEQUENCE per (org, type)
        # For DBA: CHECK (requires_approval = 0 OR is_system_type = 0) if mutually exclusive
    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_next_journal_number(self, period: AccountingPeriod = None) -> str:
        """Generate the next journal number for this type and increment the sequence."""
        from django.db import transaction

        with transaction.atomic():
            jt = JournalType.objects.select_for_update().get(pk=self.pk)
            prefix = jt.auto_numbering_prefix or ''
            suffix = jt.auto_numbering_suffix or ''
            next_num = jt.auto_numbering_next
            jt.auto_numbering_next = next_num + 1
            jt.save(update_fields=["auto_numbering_next"])
        return f"{prefix}{next_num}{suffix}"

class Journal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reversed', 'Reversed'),
    ]

    journal_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='journals'
    )
    journal_number = models.CharField(max_length=50)
    journal_type = models.ForeignKey(JournalType, on_delete=models.PROTECT)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT)
    journal_date = models.DateField()
    reference = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    source_module = models.CharField(max_length=50, null=True, blank=True)
    source_reference = models.CharField(max_length=100, null=True, blank=True)
    currency_code = models.CharField(max_length=3, default='USD')
    exchange_rate = models.DecimalField(max_digits=19, decimal_places=6, default=1)
    total_debit = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    total_credit = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_recurring = models.BooleanField(default=False)
    recurring_template = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='recurring_journals')
    is_reversal = models.BooleanField(default=False)
    reversed_journal = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversals')
    reversal_reason = models.TextField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_journals')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_journals')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_journals')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_journals')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_journals')
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_journals')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")

    class Meta:
        unique_together = ('organization', 'journal_number')
        ordering = ['-journal_date', '-journal_number']
        # For DBA: Partition monthly by journal_date
    def __str__(self):
        return f"{self.journal_number} - {self.journal_type.name}"

class JournalLine(models.Model):
    journal_line_id = models.BigAutoField(primary_key=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='lines')
    line_number = models.BigIntegerField()
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
    description = models.TextField(null=True, blank=True)
    debit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    credit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    currency_code = models.CharField(max_length=3, default='USD')
    exchange_rate = models.DecimalField(max_digits=19, decimal_places=6, default=1)
    functional_debit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    functional_credit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)  # Fixed: use ForeignKey instead of related_name
    # cost_center = models.ForeignKey('CostCenter', to_field='cost_center_id', on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True)
    tax_code = models.ForeignKey('TaxCode', on_delete=models.SET_NULL, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    memo = models.TextField(null=True, blank=True)
    reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_journal_lines')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_journal_lines')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_journal_lines')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_journal_lines')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        unique_together = ('journal', 'line_number')
        ordering = ['journal', 'line_number']
        # For DBA: Partition monthly by journal.journal_date
        # For DBA: Non-clustered index (account_id, period_id)
        # For DBA: CHECK (debit_amount = 0 OR credit_amount = 0)
    def __str__(self):
        return f"Line {self.line_number} of {self.journal.journal_number}"

class TaxAuthority(models.Model):
    authority_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT for consistency
        related_name='tax_authorities'
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    # Additional fields from second file
    country_code = models.CharField(max_length=2, null=True, blank=True)
    identifier = models.CharField(max_length=100, null=True, blank=True)
    contact_info = models.TextField(null=True, blank=True)
    api_endpoint = models.CharField(max_length=255, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    # Common fields
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tax_authorities')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_tax_authorities')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_tax_authorities')
    
    class Meta:
        unique_together = ('organization', 'code')
        verbose_name_plural = "Tax Authorities"
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    def save(self, *args, **kwargs):
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(TaxAuthority, 'code', prefix='TA', suffix='')
            self.code = code_generator.generate_code()
        super(TaxAuthority, self).save(*args, **kwargs)


class TaxType(models.Model):
    FILING_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    tax_type_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT for consistency
        related_name='tax_types'
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    # Added fields from second file
    authority = models.ForeignKey(TaxAuthority, on_delete=models.SET_NULL, null=True, blank=True)
    filing_frequency = models.CharField(max_length=50, choices=FILING_FREQUENCY_CHOICES, null=True, blank=True)
    is_system_type = models.BooleanField(default=False)
    # Common fields
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tax_types')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_tax_types')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_tax_types')
    
    class Meta:
        unique_together = ('organization', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"
    def save(self, *args, **kwargs):
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(TaxType, 'code', prefix='TT', suffix='')
            self.code = code_generator.generate_code()
        super(TaxType, self).save(*args, **kwargs)

class TaxCode(models.Model):
    tax_code_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT for consistency
        related_name='tax_codes'
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    tax_type = models.ForeignKey(TaxType, on_delete=models.PROTECT)
    description = models.TextField(null=True, blank=True)
    # Combining fields from both files
    tax_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0)  # First file version
    rate = models.DecimalField(max_digits=8, decimal_places=4, default=0)  # Second file version
    # Additional fields from second file
    is_recoverable = models.BooleanField(default=True)
    is_compound = models.BooleanField(default=False)
    effective_from = models.DateField(null=True, blank=True)  # Made nullable for backward compatibility
    effective_to = models.DateField(null=True, blank=True)
    sales_account = models.ForeignKey(ChartOfAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_tax_codes')
    purchase_account = models.ForeignKey(ChartOfAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_tax_codes')
    report_line_code = models.CharField(max_length=50, null=True, blank=True)
    # Common fields
    tax_authority = models.ForeignKey(TaxAuthority, on_delete=models.PROTECT, null=True, blank=True)  # First file version
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tax_codes')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_tax_codes')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_tax_codes')
    
    class Meta:
        unique_together = ('organization', 'code')
        
    def __str__(self):
        return f"{self.code} - {self.name} ({self.tax_rate}%)"
    
    def save(self, *args, **kwargs):
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(TaxCode, 'code', prefix='TC', suffix='')
            self.code = code_generator.generate_code()
        super(TaxCode, self).save(*args, **kwargs)

class VoucherModeConfig(models.Model):
    LAYOUT_CHOICES = [
        ('standard', 'Standard'),
        ('compact', 'Compact'),
        ('detailed', 'Detailed'),
    ]
    
    config_id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT for consistency
        related_name='voucher_mode_configs'
    )
    code = models.CharField(max_length=20)  # From first file
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    # Fields from second file
    journal_type = models.ForeignKey(JournalType, on_delete=models.CASCADE, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    layout_style = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='standard')
    show_account_balances = models.BooleanField(default=True)
    show_tax_details = models.BooleanField(default=True)
    show_dimensions = models.BooleanField(default=True)
    allow_multiple_currencies = models.BooleanField(default=False)
    require_line_description = models.BooleanField(default=True)
    default_currency = models.CharField(max_length=3, default='USD')
    # Common fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_voucher_configs')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_voucher_configs')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_voucher_configs')
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    class Meta:
        unique_together = ('organization', 'code')
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    def save(self, *args, **kwargs):
        if not self.code:
            code_generator = AutoIncrementCodeGenerator(VoucherModeConfig, 'code', prefix='VM', suffix='')
            self.code = code_generator.generate_code()
        super(VoucherModeConfig, self).save(*args, **kwargs)

# Added missing model from second file
class VoucherModeDefault(models.Model):
    default_id = models.BigAutoField(primary_key=True)
    config = models.ForeignKey(VoucherModeConfig, on_delete=models.CASCADE, related_name='defaults')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, null=True, blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, null=True, blank=True)
    default_debit = models.BooleanField(default=False)
    default_credit = models.BooleanField(default=False)
    default_amount = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    default_tax_code = models.ForeignKey(TaxCode, on_delete=models.SET_NULL, null=True, blank=True)
    default_department = models.BigIntegerField(default=0)
    # models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    default_project = models.BigIntegerField(default=0)
    # models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    default_cost_center = models.BigIntegerField(default=0)
    # models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    default_description = models.TextField(null=True, blank=True)
    is_required = models.BooleanField(default=False)
    display_order = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_voucherdefaultconfigs')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_voucherdefaultconfigs')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_voucherdefaultconfigs')
    # Add related_name to fix the reverse accessor conflicts
    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"Default for {self.config.name}"


    def __str__(self):
        return f"Default for {self.config.name}"
# Supporting models not in the original schema but needed for relationships
# class Organization(models.Model):
#     name = models.CharField(max_length=100)
#     # Add other organization fields as needed

class GeneralLedger(models.Model):
    gl_entry_id = models.BigAutoField(primary_key=True)
    organization_id = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='general_ledgers'
    )
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT)
    journal_line = models.ForeignKey(JournalLine, on_delete=models.PROTECT, related_name='gl_entries')
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT)
    transaction_date = models.DateField()
    debit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    credit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    balance_after = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    currency_code = models.CharField(max_length=3, default='USD')
    exchange_rate = models.DecimalField(max_digits=19, decimal_places=6, default=1)
    functional_debit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    functional_credit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.BigIntegerField(null=True, blank=True)
    # models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    source_module = models.CharField(max_length=50, null=True, blank=True)
    source_reference = models.CharField(max_length=100, null=True, blank=True)
    is_adjustment = models.BooleanField(default=False)
    is_closing_entry = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    rowversion = models.BinaryField(editable=False, null=True, blank=True, help_text="For MSSQL: ROWVERSION for optimistic concurrency.")
    
    # archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    # created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['transaction_date', 'created_at']
        indexes = [
            models.Index(fields=['account', 'transaction_date']),
            models.Index(fields=['transaction_date', 'account']),
        ]
        # For DBA: CLUSTERED COLUMNSTORE once >10M rows; narrow row-store NC index on (org, account, transaction_date)
        # For DBA: Monthly partitioning; move cold partitions to slower filegroup
        # For DBA: Make balance_after a PERSISTED computed column

    def __str__(self):
        return f"GL Entry {self.gl_entry_id} for {self.account.account_code}"
