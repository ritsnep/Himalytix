from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from usermanagement.models import CustomUser, Organization
User = get_user_model()

class FiscalYear(models.Model):
    fiscal_year_id = models.BigAutoField(primary_key=True)  # SERIAL IDENTITY
    organization_id = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='fiscal_years'
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='open')
    is_current = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.IntegerField(null=True, blank=True)  # You may change to ForeignKey(User) later
    created_at = models.DateTimeField(auto_now_add=True)  # DEFAULT NOW()
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)  # Or ForeignKey(User)
    updated_by = models.IntegerField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.IntegerField(null=True, blank=True)  # You may change to ForeignKey(User) later
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'fiscal_years'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountingPeriod(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('adjustment', 'Adjustment'),
    ]

    period_id = models.AutoField(primary_key=True)
    fiscal_year = models.ForeignKey('FiscalYear', on_delete=models.PROTECT, related_name='periods')
    period_number = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(16)])
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_adjustment_period = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_periods')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_periods')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_periods')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('fiscal_year', 'period_number')
        ordering = ['fiscal_year', 'period_number']

    def __str__(self):
        return f"{self.fiscal_year.name} - {self.name}"

class Department(models.Model):
    name = models.CharField(max_length=100)
    # Add other department fields as needed
class Project(models.Model):
    project_id = models.AutoField(primary_key=True)  # Add this line
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')  # Add organization relationship
    code = models.CharField(max_length=20, unique=True)  # Add code field
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.code} - {self.name}"
class CostCenter(models.Model):
    name = models.CharField(max_length=100)
    # Add other cost center fields as needed

class AccountType(models.Model):
    NATURE_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    account_type_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES)
    classification = models.CharField(max_length=50)
    balance_sheet_category = models.CharField(max_length=50, null=True, blank=True)
    income_statement_category = models.CharField(max_length=50, null=True, blank=True)
    cash_flow_category = models.CharField(max_length=50, null=True, blank=True)
    system_type = models.BooleanField(default=True)
    display_order = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    # Add related_name to fix the reverse accessor conflicts
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_account_types')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_account_types')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_account_types')
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ChartOfAccount(models.Model):
    account_id = models.AutoField(primary_key=True)
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
    currency_code = models.CharField(max_length=3, default='USD')
    opening_balance = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    current_balance = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    reconciled_balance = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    last_reconciled_date = models.DateTimeField(null=True, blank=True)
    allow_manual_journal = models.BooleanField(default=True)
    account_level = models.SmallIntegerField(default=1)
    tree_path = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_accounts')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_accounts')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_accounts')
    
    class Meta:
        unique_together = ('organization', 'account_code')
        ordering = ['account_code']

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class CurrencyExchangeRate(models.Model):
    rate_id = models.AutoField(primary_key=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='currency_exchange_rates'
    )
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate_date = models.DateField()
    exchange_rate = models.DecimalField(max_digits=19, decimal_places=6)
    is_average_rate = models.BooleanField(default=False)
    source = models.CharField(max_length=50, default='manual')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    # Add related_name to fix the reverse accessor conflicts
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_exchange_rates')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_exchange_rates')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_exchange_rates')
    
    class Meta:
        unique_together = ('organization', 'from_currency', 'to_currency', 'rate_date')

    def __str__(self):
        return f"{self.from_currency}/{self.to_currency} @ {self.exchange_rate} on {self.rate_date}"


class JournalType(models.Model):
    journal_type_id = models.AutoField(primary_key=True)
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
    auto_numbering_next = models.IntegerField(default=1)
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
    
    class Meta:
        unique_together = ('organization', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class Journal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reversed', 'Reversed'),
    ]

    journal_id = models.AutoField(primary_key=True)
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

    class Meta:
        unique_together = ('organization', 'journal_number')
        ordering = ['-journal_date', '-journal_number']

    def __str__(self):
        return f"{self.journal_number} - {self.journal_type.name}"


# class JournalLine(models.Model):
#     journal_line_id = models.AutoField(primary_key=True)
#     journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='lines')
#     line_number = models.IntegerField()
#     account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
#     description = models.TextField(null=True, blank=True)
#     debit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
#     credit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
#     currency_code = models.CharField(max_length=3, default='USD')
#     exchange_rate = models.DecimalField(max_digits=19, decimal_places=6, default=1)
#     functional_debit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
#     functional_credit_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0)
#     department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
#     project =  models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True,related_name='journal_lines_project')
#     cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True)
#     tax_code = models.ForeignKey('TaxCode', on_delete=models.SET_NULL, null=True, blank=True)
#     tax_rate = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
#     tax_amount = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
#     memo = models.TextField(null=True, blank=True)
#     reconciled = models.BooleanField(default=False)
#     reconciled_at = models.DateTimeField(null=True, blank=True)
#     reconciled_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_journal_lines')
#     created_at = models.DateTimeField(default=timezone.now)
#     updated_at = models.DateTimeField(null=True, blank=True)
#     created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_journal_lines')
#     updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_journal_lines')
#     is_archived = models.BooleanField(default=False)
#     archived_at = models.DateTimeField(null=True, blank=True)
#     archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_journal_lines')
    
#     class Meta:
#         unique_together = ('journal', 'line_number')
#         ordering = ['journal', 'line_number']

#     def __str__(self):
#         return f"Line {self.line_number} of {self.journal.journal_number}"


# Fixed JournalLine model - this is where the issue was occurring
class JournalLine(models.Model):
    journal_line_id = models.AutoField(primary_key=True)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='lines')
    line_number = models.IntegerField()
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
    
    class Meta:
        unique_together = ('journal', 'line_number')
        ordering = ['journal', 'line_number']

    def __str__(self):
        return f"Line {self.line_number} of {self.journal.journal_number}"


class TaxAuthority(models.Model):
    authority_id = models.AutoField(primary_key=True)
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


class TaxType(models.Model):
    FILING_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    tax_type_id = models.AutoField(primary_key=True)
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


class TaxCode(models.Model):
    tax_code_id = models.AutoField(primary_key=True)
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


class VoucherModeConfig(models.Model):
    LAYOUT_CHOICES = [
        ('standard', 'Standard'),
        ('compact', 'Compact'),
        ('detailed', 'Detailed'),
    ]
    
    config_id = models.AutoField(primary_key=True)
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
    
    class Meta:
        unique_together = ('organization', 'code')
        
    def __str__(self):
        return f"{self.code} - {self.name}"


# Added missing model from second file
class VoucherModeDefault(models.Model):
    default_id = models.AutoField(primary_key=True)
    config = models.ForeignKey(VoucherModeConfig, on_delete=models.CASCADE, related_name='defaults')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, null=True, blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, null=True, blank=True)
    default_debit = models.BooleanField(default=False)
    default_credit = models.BooleanField(default=False)
    default_amount = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    default_tax_code = models.ForeignKey(TaxCode, on_delete=models.SET_NULL, null=True, blank=True)
    default_department = models.IntegerField(default=0)
    # models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    default_project = models.IntegerField(default=0)
    # models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    default_cost_center = models.IntegerField(default=0)
    # models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    default_description = models.TextField(null=True, blank=True)
    is_required = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
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
    project = models.IntegerField(null=True, blank=True)
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
    
    # archived_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    # created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['transaction_date', 'created_at']
        indexes = [
            models.Index(fields=['account', 'transaction_date']),
            models.Index(fields=['transaction_date', 'account']),
        ]

    def __str__(self):
        return f"GL Entry {self.gl_entry_id} for {self.account.account_code}"
