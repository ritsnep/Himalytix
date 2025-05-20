# forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    AccountType, CostCenter, Department, Journal, JournalLine, JournalType, ChartOfAccount,
    AccountingPeriod, Project, TaxCode, VoucherModeConfig, VoucherModeDefault
)

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