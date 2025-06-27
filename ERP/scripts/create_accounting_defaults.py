from django.utils import timezone
import logging

# WARNING: This script may create overlapping data if run with create_default_data. Review both scripts before running in production.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from usermanagement.models import Organization
from accounting.models import (
    JournalType, VoucherModeConfig, VoucherModeDefault,
    AccountType, ChartOfAccount, Department, Project, CostCenter
)

def create_defaults():
    # First check if organization exists
    org = Organization.objects.first()
    
    if not org:
        # Create default organization
        org = Organization.objects.create(
            tenant=1,
            name="Default Organization",
            code="DEFAULT",
            type="company",
            is_active=True,
            fiscal_year_start_month=1,
            fiscal_year_start_day=1,
            base_currency_code="USD",
            status="active"
        )

    # Create default account types
    account_types = {
        'AS': ('Assets', 'asset', 'Balance Sheet', 1),
        'LI': ('Liabilities', 'liability', 'Balance Sheet', 2),
        'EQ': ('Equity', 'equity', 'Balance Sheet', 3),
        'IN': ('Income', 'income', 'Income Statement', 4),
        'EX': ('Expenses', 'expense', 'Income Statement', 5),
    }

    created_types = {}
    for code, (name, nature, classification, order) in account_types.items():
        at, _ = AccountType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'nature': nature,
                'classification': classification,
                'display_order': order,
                'system_type': True
            }
        )
        created_types[code] = at

    # Create basic chart of accounts
    accounts = {
        '1000': ('Cash', 'AS', True),
        '1100': ('Bank', 'AS', True),
        '2000': ('Accounts Payable', 'LI', True),
        '3000': ('Capital', 'EQ', True),
        '4000': ('Sales', 'IN', True),
        '5000': ('Cost of Sales', 'EX', True),
        '6000': ('Expenses', 'EX', True),
    }

    for code, (name, type_code, active) in accounts.items():
        ChartOfAccount.objects.get_or_create(
            organization=org,
            account_code=code,
            defaults={
                'account_name': name,
                'account_type': created_types[type_code],
                'is_active': active,
                'allow_manual_journal': True
            }
        )

    # Create journal types
    journal_types = {
        'GJ': ('General Journal', 'For miscellaneous transactions', 'GJ'),
        'PJ': ('Payment Journal', 'For payment transactions', 'PV'),
        'RJ': ('Receipt Journal', 'For receipt transactions', 'RV'),
        'SJ': ('Sales Journal', 'For sales transactions', 'SV'),
        'PU': ('Purchase Journal', 'For purchase transactions', 'PV'),
    }

    created_journals = {}
    for code, (name, desc, prefix) in journal_types.items():
        jt, _ = JournalType.objects.get_or_create(
            organization=org,
            code=code,
            defaults={
                'name': name,
                'description': desc,
                'auto_numbering_prefix': prefix,
                'is_system_type': True,
                'is_active': True
            }
        )
        created_journals[code] = jt

    # Create voucher configurations
    voucher_configs = {
        'GV': ('General Voucher', 'GJ', True),
        'PV': ('Payment Voucher', 'PJ', False),
        'RV': ('Receipt Voucher', 'RJ', False),
        'SV': ('Sales Voucher', 'SJ', False),
        'PI': ('Purchase Invoice', 'PU', False),
    }

    for code, (name, jtype, is_default) in voucher_configs.items():
        config, _ = VoucherModeConfig.objects.get_or_create(
            organization=org,
            code=code,
            defaults={
                'name': name,
                'journal_type': created_journals[jtype],
                'is_default': is_default,
                'layout_style': 'standard',
                'show_account_balances': True,
                'show_tax_details': True,
                'show_dimensions': True,
                'require_line_description': True,
                'default_currency': 'USD'
            }
        )

        # Create default lines based on voucher type
        if code == 'GV':
            VoucherModeDefault.objects.get_or_create(
                config=config,
                display_order=1,
                defaults={
                    'default_debit': True,
                    'is_required': True,
                    'default_description': 'Debit Entry'
                }
            )
            VoucherModeDefault.objects.get_or_create(
                config=config,
                display_order=2,
                defaults={
                    'default_credit': True,
                    'is_required': True,
                    'default_description': 'Credit Entry'
                }
            )
        elif code == 'PV':
            VoucherModeDefault.objects.get_or_create(
                config=config,
                display_order=1,
                defaults={
                    'account': ChartOfAccount.objects.get(organization=org, account_code='1000'),
                    'default_credit': True,
                    'is_required': True,
                    'default_description': 'Cash Payment'
                }
            )
        elif code == 'RV':
            VoucherModeDefault.objects.get_or_create(
                config=config,
                display_order=1,
                defaults={
                    'account': ChartOfAccount.objects.get(organization=org, account_code='1000'),
                    'default_debit': True,
                    'is_required': True,
                    'default_description': 'Cash Receipt'
                }
            )

if __name__ == '__main__':
    create_defaults()
