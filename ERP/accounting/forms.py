# forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    AccountType, CostCenter, Currency, Department, Journal, JournalLine, JournalType, ChartOfAccount,
    AccountingPeriod, Project, TaxAuthority, TaxCode, TaxType, VoucherModeConfig, VoucherModeDefault, CurrencyExchangeRate
)
from django import forms
from .models import FiscalYear
from .utils import get_active_currency_choices


# class FiscalYearForm(forms.ModelForm):
#     class Meta:
#         model = FiscalYear
#         fields = ('code',  'name', 'start_date', 'end_date', 'status', 'is_current')
class FiscalYearForm(forms.ModelForm):
    code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True,
        })
    )
    
    class Meta:
        model = FiscalYear
        fields = ('code', 'name', 'start_date', 'end_date', 'status', 'is_current','is_default')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate code for new instances
        if not self.instance.pk:
            from .models import AutoIncrementCodeGenerator
            code_generator = AutoIncrementCodeGenerator(FiscalYear, 'code', prefix='FY', suffix='')
            generated_code = code_generator.generate_code()
            self.initial['code'] = generated_code
            self.fields['code'].initial = generated_code


# New forms below
class AccountingPeriodForm(forms.ModelForm):
    class Meta:
        model = AccountingPeriod
        fields = ('name', 'period_number', 'start_date', 'end_date', 'status', 'is_current')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'period_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProjectForm(forms.ModelForm):
    code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True,
        })
    )
    
    class Meta:
        model = Project
        fields = ('code', 'name', 'description', 'is_active', 'start_date', 'end_date')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Generate code for new instances
        if not self.instance.pk:
            from .models import AutoIncrementCodeGenerator
            code_generator = AutoIncrementCodeGenerator(Project, 'code', prefix='PRJ', suffix='')
            generated_code = code_generator.generate_code()
            self.initial['code'] = generated_code
            self.fields['code'].initial = generated_code
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class CostCenterForm(forms.ModelForm):
    code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True,
        })
    )
    
    class Meta:
        model = CostCenter
        fields = ('code', 'name', 'description', 'is_active', 'start_date', 'end_date')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Generate code for new instances
        if not self.instance.pk:
            from .models import AutoIncrementCodeGenerator
            code_generator = AutoIncrementCodeGenerator(CostCenter, 'code', prefix='CC', suffix='')
            generated_code = code_generator.generate_code()
            self.initial['code'] = generated_code
            self.fields['code'].initial = generated_code
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class AccountTypeForm(forms.ModelForm):
    class Meta:
        model = AccountType
        fields = ('name', 'nature', 'classification', 'balance_sheet_category', 
                  'income_statement_category', 'display_order', 'system_type')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'nature': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.TextInput(attrs={'class': 'form-control'}),
            'balance_sheet_category': forms.TextInput(attrs={'class': 'form-control'}),
            'income_statement_category': forms.TextInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'system_type': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ChartOfAccountForm(forms.ModelForm):
    class Meta:
        model = ChartOfAccount
        fields = [
            'account_code', 'account_name', 'account_type', 'parent_account',
            'description', 'is_active', 'is_bank_account', 'is_control_account',
            'control_account_type', 'require_cost_center', 'require_project',
            'require_department', 'default_tax_code', 'currency_code',
            'allow_manual_journal'
        ]
        widgets = {
            'account_code': forms.TextInput(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'parent_account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_bank_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_control_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'control_account_type': forms.TextInput(attrs={'class': 'form-control'}),
            'require_cost_center': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_project': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_department': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_tax_code': forms.TextInput(attrs={'class': 'form-control'}),
            'currency_code': forms.Select(attrs={'class': 'form-select'}),
            'allow_manual_journal': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Filter parent choices to only show accounts from the same organization
            self.fields['parent_account'].queryset = ChartOfAccount.objects.filter(
                organization=self.organization,
                is_active=True
            )
            # Filter account type choices
            self.fields['account_type'].queryset = AccountType.objects.filter(
                is_archived=False
            )
            
            # Set up currency choices
            self.fields['currency_code'].widget = forms.Select(attrs={'class': 'form-select'})
            self.fields['currency_code'].choices = [
                (currency.code, f"{currency.code} - {currency.name}") 
                for currency in Currency.objects.filter(is_active=True)
            ]

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ('currency_code', 'currency_name', 'symbol', 'is_active')
        widgets = {
            'currency_code': forms.TextInput(attrs={'class': 'form-control'}),
            'currency_name': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CurrencyExchangeRateForm(forms.ModelForm):
    class Meta:
        model = CurrencyExchangeRate
        fields = ('from_currency', 'to_currency', 'rate_date', 'exchange_rate', 'is_average_rate', 'source')
        widgets = {
            'from_currency': forms.Select(attrs={'class': 'form-select'}),
            'to_currency': forms.Select(attrs={'class': 'form-select'}),
            'rate_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'is_average_rate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Populate currency choices
        
        currency_choices = get_active_currency_choices()
        self.fields['from_currency'].choices = currency_choices
        self.fields['to_currency'].choices = currency_choices
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class JournalTypeForm(forms.ModelForm):
    class Meta:
        model = JournalType
        fields = ('code', 'name', 'description', 'auto_numbering_prefix', 
                  'auto_numbering_suffix', 'auto_numbering_next', 
                  'is_system_type', 'requires_approval', 'is_active')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'auto_numbering_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'auto_numbering_suffix': forms.TextInput(attrs={'class': 'form-control'}),
            'auto_numbering_next': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_system_type': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class TaxAuthorityForm(forms.ModelForm):
    class Meta:
        model = TaxAuthority
        fields = ('name', 'country_code', 'description', 'is_active', 'is_default')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'country_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class TaxTypeForm(forms.ModelForm):
    class Meta:
        model = TaxType
        fields = ('name', 'authority', 'description', 'filing_frequency', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'authority': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'filing_frequency': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filter tax authorities by organization
        if self.organization:
            self.fields['authority'].queryset = TaxAuthority.objects.filter(
                organization=self.organization
            )
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class TaxCodeForm(forms.ModelForm):
    class Meta:
        model = TaxCode
        fields = ('name', 'tax_type', 'tax_authority', 'tax_rate', 'rate',
                  'description', 'is_active', 'is_recoverable', 'effective_from')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_authority': forms.Select(attrs={'class': 'form-select'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_recoverable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'effective_from': forms.TextInput(attrs={'class': 'form-control datepicker'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filter related models by organization
        if self.organization:
            self.fields['tax_type'].queryset = TaxType.objects.filter(
                organization=self.organization
            )
            self.fields['tax_authority'].queryset = TaxAuthority.objects.filter(
                organization=self.organization
            )
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class VoucherModeConfigForm(forms.ModelForm):
    class Meta:
        model = VoucherModeConfig
        fields = ('name', 'description', 'is_default', 'layout_style', 
                  'show_account_balances', 'show_tax_details', 'show_dimensions', 
                  'allow_multiple_currencies', 'require_line_description', 'default_currency')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'layout_style': forms.Select(attrs={'class': 'form-select'}),
            'show_account_balances': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_tax_details': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_dimensions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_multiple_currencies': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_line_description': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_currency': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Populate currency choices
        self.fields['default_currency'].choices = [
            (currency.currency_code, f"{currency.currency_code} - {currency.currency_name}") 
            for currency in Currency.objects.filter(is_active=True)
        ]
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance
class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = [
            'journal_type', 'period', 'journal_date', 
            'reference', 'description', 'currency_code',
            'exchange_rate'
        ]
        widgets = {
            'journal_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['journal_type'].queryset = JournalType.objects.filter(
                organization=organization,
                is_active=True
            )
            self.fields['period'].queryset = AccountingPeriod.objects.filter(
                fiscal_year__organization=organization,
                status='open'
            )

class JournalLineForm(forms.ModelForm):
    class Meta:
        model = JournalLine
        fields = [
            'account', 'description', 'debit_amount', 'credit_amount',
            'currency_code', 'exchange_rate', 'department', 'project', 'cost_center',
            'tax_code', 'tax_rate', 'tax_amount', 'memo'
        ]

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(organization=organization)
            self.fields['department'].queryset = Department.objects.filter(organization=organization)
            self.fields['project'].queryset = Project.objects.filter(organization=organization)
            self.fields['cost_center'].queryset = CostCenter.objects.filter(organization=organization)
            self.fields['tax_code'].queryset = TaxCode.objects.filter(organization=organization)

# forms.py (continued)
JournalLineFormSet = inlineformset_factory(
    Journal, JournalLine,
    form=JournalLineForm,
    extra=1,
    can_delete=True,
    fields=[
        'account', 'description', 'debit_amount', 
        'credit_amount', 'department', 'project',
        'cost_center', 'tax_code', 'memo'
    ]
)

class VoucherModeConfigForm(forms.ModelForm):
    class Meta:
        model = VoucherModeConfig
        fields = [
            'name', 'description', 'journal_type', 'is_default',
            'layout_style', 'show_account_balances', 'show_tax_details',
            'show_dimensions', 'allow_multiple_currencies',
            'require_line_description', 'default_currency'
        ]
    
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['journal_type'].queryset = JournalType.objects.filter(
                organization=organization,
                is_active=True
            )

class VoucherModeDefaultForm(forms.ModelForm):
    account_code = forms.CharField(required=False)
    account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.all(),
        required=False
    )
    
    class Meta:
        model = VoucherModeDefault
        fields = [
            'account', 'account_type', 'default_debit', 'default_credit',
            'default_amount', 'default_tax_code', 'default_department',
            'default_project', 'default_cost_center', 'default_description',
            'is_required', 'display_order'
        ]
        widgets = {
            'account': forms.HiddenInput(),
            'default_description': forms.TextInput(),
        }
    
    def __init__(self, *args, organization=None, config_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['default_department'].queryset = Department.objects.filter(
                organization=organization
            )
            self.fields['default_project'].queryset = Project.objects.filter(
                organization=organization
            )
            self.fields['default_cost_center'].queryset = CostCenter.objects.filter(
                organization=organization
            )
            self.fields['default_tax_code'].queryset = TaxCode.objects.filter(
                organization=organization,
                is_active=True
            )
            
            if config_id:
                config = VoucherModeConfig.objects.get(pk=config_id)
                self.fields['account_type'].queryset = AccountType.objects.filter(
                    chartofaccount__organization=organization
                ).distinct()