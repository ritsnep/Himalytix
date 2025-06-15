# forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    AccountType, CostCenter, Currency, Department, Journal, JournalLine, JournalType, ChartOfAccount,
    AccountingPeriod, Project, TaxAuthority, TaxCode, TaxType, VoucherModeConfig, VoucherModeDefault, CurrencyExchangeRate,
    GeneralLedger
)
from django import forms
from .models import FiscalYear
from .utils import get_active_currency_choices
from .forms_mixin import BootstrapFormMixin


# class FiscalYearForm(forms.ModelForm):
#     class Meta:
#         model = FiscalYear
#         fields = ('code',  'name', 'start_date', 'end_date', 'status', 'is_current')
class FiscalYearForm(BootstrapFormMixin, forms.ModelForm):
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
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        # Generate code for new instances
        if not self.instance.pk:
            from .models import AutoIncrementCodeGenerator
            code_generator = AutoIncrementCodeGenerator(FiscalYear, 'code', prefix='FY', suffix='')
            generated_code = code_generator.generate_code()
            self.initial['code'] = generated_code
            self.fields['code'].initial = generated_code


# New forms below
class AccountingPeriodForm(BootstrapFormMixin, forms.ModelForm):
    fiscal_year = forms.ModelChoiceField(
        queryset=FiscalYear.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Fiscal Year"
    )
    class Meta:
        model = AccountingPeriod
        fields = ('fiscal_year', 'name', 'period_number', 'start_date', 'end_date', 'status', 'is_current')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'period_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control datepicker'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(organization=self.organization)
        else:
            self.fields['fiscal_year'].queryset = FiscalYear.objects.none()
        
class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProjectForm(BootstrapFormMixin, forms.ModelForm):
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

class CostCenterForm(BootstrapFormMixin, forms.ModelForm):
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

# class AccountTypeForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = AccountType
#         fields = ('name', 'nature', 'classification', 'balance_sheet_category', 
#                   'income_statement_category', 'display_order', 'system_type')
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'nature': forms.Select(attrs={'class': 'form-select'}),
#             'classification': forms.TextInput(attrs={'class': 'form-control'}),
#             'balance_sheet_category': forms.TextInput(attrs={'class': 'form-control'}),
#             'income_statement_category': forms.TextInput(attrs={'class': 'form-control'}),
#             'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
#             'system_type': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }

class AccountTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AccountType
        fields = (
            'name',
            'nature',
            'classification',
            'balance_sheet_category',
            'income_statement_category',
            'display_order',
            'root_code_prefix',
            'root_code_step',
            'system_type',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'nature': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.TextInput(attrs={'class': 'form-control'}),
            'balance_sheet_category': forms.TextInput(attrs={'class': 'form-control'}),
            'income_statement_category': forms.TextInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'root_code_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'root_code_step': forms.NumberInput(attrs={'class': 'form-control'}),
            'system_type': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class ChartOfAccountForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ChartOfAccount
        fields = [
            'organization',
            'parent_account',
            'account_type',
            'account_code',
            'account_name',
            'description',
            'is_active',
            'is_bank_account',
            'is_control_account',
            'control_account_type',
            'require_cost_center',
            'require_project',
            'require_department',
            'default_tax_code',
            'currency',
            'opening_balance',
            'current_balance',
            'reconciled_balance',
            'last_reconciled_date',
            'allow_manual_journal',
            'account_level',
            'tree_path',
            'display_order'
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
            'currency': forms.Select(attrs={'class': 'form-select'}),
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
            currency_choices = [(currency.currency_code, f"{currency.currency_code} - {currency.currency_name}") 
                               for currency in Currency.objects.filter(is_active=True)]
            self.fields['currency'].widget = forms.Select(attrs={'class': 'form-select'})
            self.fields['currency'].choices = currency_choices

        # Filter AccountType if parent is selected
        parent = self.initial.get('parent_account') or self.data.get('parent_account')
        if parent:
            try:
                parent_obj = ChartOfAccount.objects.get(pk=parent)
                self.fields['account_type'].queryset = AccountType.objects.filter(
                    pk=parent_obj.account_type.pk
                )
                self.parent_account_type = parent_obj.account_type
            except ChartOfAccount.DoesNotExist:
                self.parent_account_type = None
        else:
            self.parent_account_type = None

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent_account')
        account_type = cleaned_data.get('account_type')
        if parent and account_type and parent.account_type != account_type:
            self.add_error('account_type', "Account type must match the parent account's type.")
        return cleaned_data

class CurrencyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Currency
        fields = ('currency_code', 'currency_name', 'symbol', 'is_active')
        widgets = {
            'currency_code': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            'currency_name': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_currency_code(self):
        code = self.cleaned_data['currency_code']
        return code.upper()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # If editing existing currency
            self.fields['currency_code'].widget.attrs['readonly'] = True

class CurrencyExchangeRateForm(BootstrapFormMixin, forms.ModelForm):
    from_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        empty_label="Select From Currency",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'required',
            'data-pristine-required-message': "Please select a 'from' currency."
        })
    )
    to_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        empty_label="Select To Currency",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'required',
            'data-pristine-required-message': "Please select a 'to' currency."
        })
    )
    rate_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'required': 'required',
            'data-pristine-required-message': "Please select a rate date."
        })
    )
    exchange_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'required': 'required',
            'data-pristine-required-message': "Please enter an exchange rate.",
            'step': '0.000001'
        })
    )
    is_average_rate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    source = forms.ChoiceField(
        choices=[('manual', 'Manual'), ('api', 'API')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CurrencyExchangeRate
        fields = ['from_currency', 'to_currency', 'rate_date', 'exchange_rate', 'is_average_rate', 'source']

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['from_currency'].queryset = Currency.objects.filter(is_active=True)
            self.fields['to_currency'].queryset = Currency.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        from_currency = cleaned_data.get('from_currency')
        to_currency = cleaned_data.get('to_currency')
        rate_date = cleaned_data.get('rate_date')

        if from_currency and to_currency and rate_date:
            if from_currency == to_currency:
                raise forms.ValidationError("From and To currencies cannot be the same.")

            # Check for duplicate exchange rate
            if CurrencyExchangeRate.objects.filter(
                organization=self.organization,
                from_currency=from_currency,
                to_currency=to_currency,
                rate_date=rate_date
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError("An exchange rate for this currency pair and date already exists.")

        return cleaned_data

class JournalTypeForm(BootstrapFormMixin, forms.ModelForm):
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

class TaxAuthorityForm(BootstrapFormMixin, forms.ModelForm):
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

class TaxTypeForm(BootstrapFormMixin, forms.ModelForm):
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

class TaxCodeForm(BootstrapFormMixin, forms.ModelForm):
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

class VoucherModeConfigForm(BootstrapFormMixin, forms.ModelForm):
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
        currency_choices = [(currency.currency_code, f"{currency.currency_code} - {currency.currency_name}") 
                           for currency in Currency.objects.filter(is_active=True)]
        self.fields['default_currency'].choices = currency_choices

        # Fix: use self.organization instead of undefined variable
        if self.organization:
            self.fields['journal_type'].queryset = JournalType.objects.filter(
                organization=self.organization,
                is_active=True
            )
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance

class JournalForm(BootstrapFormMixin, forms.ModelForm):
    # Override currency_code to be a ChoiceField populated from Currency model for a dropdown
    currency_code = forms.ChoiceField(
        choices=[], # Will be populated dynamically in __init__
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'required',
            'data-pristine-required-message': "Please select a currency."
        })
    )

    class Meta:
        model = Journal
        fields = [
            'journal_type', 'period', 'journal_date', 
            'reference', 'description', 'currency_code',
            'exchange_rate'
        ]
        widgets = {
            'journal_type': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'journal_date': forms.DateInput(attrs={
                'class': 'form-control datepicker', # Ensure datepicker class is applied
                'required': 'required',
                'data-pristine-required-message': "Please select a journal date."
            }),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # currency_code widget is overridden above
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'required': 'required',
                'data-pristine-required-message': "Please enter an exchange rate.",
                'data-pristine-min-message': "Exchange rate must be positive.",
                'min': '0.000001' # Client-side validation for non-zero rate
            }),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
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
            
            # Populate currency_code choices from active Currency objects
            currency_choices = [(c.currency_code, f"{c.currency_code} - {c.currency_name}")
                                for c in Currency.objects.filter(is_active=True)]
            
            # Add an empty default choice if not already populated (for create view)
            if not self.instance.pk and not self.initial.get('currency_code'):
                 self.fields['currency_code'].choices = [('', '---------')] + currency_choices
            else:
                self.fields['currency_code'].choices = currency_choices
            
            # Ensure the initial value for currency_code is correctly set for existing instances
            if self.instance.pk and self.instance.currency_code:
                self.initial['currency_code'] = self.instance.currency_code


class JournalLineForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = JournalLine
        fields = [
            'account', 'description', 'debit_amount', 'credit_amount',
            'currency_code', 'exchange_rate', 'department', 'project', 'cost_center',
            'tax_code', 'tax_rate', 'tax_amount', 'memo'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required',
                'data-pristine-required-message': 'Please select an account.'
            }),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01', # Allow decimal values
                'data-pristine-required-message': 'Debit amount is required.',
                'data-pristine-min-message': 'Debit amount must be non-negative.',
                'min': '0', 
                'data-pristine-number-message': 'Please enter a valid number.'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01', # Allow decimal values
                'data-pristine-required-message': 'Credit amount is required.',
                'data-pristine-min-message': 'Credit amount must be non-negative.',
                'min': '0', 
                'data-pristine-number-message': 'Please enter a valid number.'
            }),
            # Set widget for currency_code for JournalLineForm too
            'currency_code': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required', # Make it required at line level too
                'data-pristine-required-message': 'Please select a currency for the line.'
            }),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'required': 'required', # Make it required at line level too
                'data-pristine-required-message': 'Please enter exchange rate for the line.',
                'data-pristine-min-message': 'Exchange rate must be positive.',
                'min': '0.000001'
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'cost_center': forms.Select(attrs={'class': 'form-select'}),
            'tax_code': forms.Select(attrs={'class': 'form-select'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'memo': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(organization=organization)
            self.fields['department'].queryset = Department.objects.filter(organization=organization)
            self.fields['project'].queryset = Project.objects.filter(organization=organization)
            self.fields['cost_center'].queryset = CostCenter.objects.filter(organization=organization)
            self.fields['tax_code'].queryset = TaxCode.objects.filter(organization=organization)
            
            # Populate currency_code choices for JournalLineForm
            currency_choices = [(c.currency_code, f"{c.currency_code} - {c.currency_name}")
                                for c in Currency.objects.filter(is_active=True)]
            self.fields['currency_code'].choices = [('', '---------')] + currency_choices
            
        # Custom validation: ensure either debit or credit is present, but not both or neither.
        # This will be validated server-side.
        self.fields['debit_amount'].required = False # Allow one to be zero if other is non-zero
        self.fields['credit_amount'].required = False # Allow one to be zero if other is non-zero

    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit_amount')
        credit = cleaned_data.get('credit_amount')

        # Convert None to 0 for consistent comparison
        debit = debit if debit is not None else 0
        credit = credit if credit is not None else 0
        
        if (debit == 0 and credit == 0) or (debit > 0 and credit > 0):
            # Add error to the form directly
            raise forms.ValidationError("A journal line must have either a Debit amount or a Credit amount, but not both, and not neither.")
        
        return cleaned_data

# Ensure JournalLineFormSet passes organization to each form
JournalLineFormSet = inlineformset_factory(
    Journal, JournalLine,
    form=JournalLineForm,
    extra=1, # Start with one empty form
    can_delete=True,
    fields=[
        'account', 'description', 'debit_amount', 
        'credit_amount', 'department', 'project',
        'cost_center', 'tax_code', 'memo', 'currency_code', 'exchange_rate' # Include these fields
    ]
)

class VoucherModeConfigForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = VoucherModeConfig
        fields = [
            'name', 'description', 'journal_type', 'is_default',
            'layout_style', 'show_account_balances', 'show_tax_details',
            'show_dimensions', 'allow_multiple_currencies',
            'require_line_description', 'default_currency'
        ]
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if self.organization:
            self.fields['journal_type'].queryset = JournalType.objects.filter(
                organization=self.organization,
                is_active=True
            )

class VoucherModeDefaultForm(BootstrapFormMixin, forms.ModelForm):
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
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        config_id = kwargs.pop('config_id', None)
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

        # Prepopulate account_code for existing instances
        if self.instance.pk and self.instance.account:
            self.fields['account_code'].initial = self.instance.account.account_code

    def clean(self):
        cleaned_data = super().clean()
        account_code = cleaned_data.get('account_code')
        if account_code and self.organization:
            try:
                account = ChartOfAccount.objects.get(
                    organization=self.organization,
                    account_code=account_code
                )
                cleaned_data['account'] = account
            except ChartOfAccount.DoesNotExist:
                self.add_error('account_code', 'Invalid account code.')
        return cleaned_data

class GeneralLedgerForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = GeneralLedger
        fields = '__all__'
        widgets = {
            'transaction_date': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation here
        return cleaned_data