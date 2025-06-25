import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

import os
import sys

from django.db import IntegrityError
from django.core.exceptions import ValidationError

print("Before adding erp to sys.path:")
print(sys.path)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("After adding erp to sys.path:")
print(sys.path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()


from django.contrib.auth import get_user_model
from usermanagement.models import CustomUser, Organization, Module, Entity, Permission, Role, UserRole
from accounting.models import (
    FiscalYear, AccountingPeriod, Department, Project, CostCenter,
    AccountType, ChartOfAccount, Currency, JournalType, TaxAuthority, 
    TaxType, TaxCode, VoucherModeConfig
)
from django.utils import timezone

def create_default_data():
    """
    Create default data for the accounting system with Nepali fiscal year and NPR currency
    """
    print("Starting to create default data for Nepal...")
    
    # Get the superuser (assuming there's only one, or get the first one)
    try:
        superuser = CustomUser.objects.filter(is_superuser=True).first()
        if not superuser:
            print("No superuser found. Please create a superuser first.")
            return
        print(f"Using superuser: {superuser.username}")
    except Exception as e:
        print(f"Error getting superuser: {e}")
        return
    
    # Create default organization if it doesn't exist
    organization, created = Organization.objects.get_or_create(
        name='Nepali Accounting System',
        code='NEPAL-001',
        type='company',
        legal_name='Nepali Accounting System Pvt. Ltd.',
        tax_id='NP-123456',
        registration_number='REG-2024-001',
        industry_code='ACCT',
        fiscal_year_start_month=4,  # Example: Baisakh (Nepali FY start)
        fiscal_year_start_day=1,
        base_currency_code='NPR',
        status='active',
        is_active=True,
        defaults={
            # Only optional fields not in the main arguments, if any
        }
    )
    if created:
        print(f"Created default organization: {organization.name}")
    else:
        print(f"Using existing organization: {organization.name}")
    
    # Create default currencies with NPR as primary
    currencies_data = [
        {'currency_code': 'NPR', 'currency_name': 'Nepalese Rupee', 'symbol': 'Rs'},
        {'currency_code': 'USD', 'currency_name': 'US Dollar', 'symbol': '$'},
        {'currency_code': 'EUR', 'currency_name': 'Euro', 'symbol': '€'},
        {'currency_code': 'INR', 'currency_name': 'Indian Rupee', 'symbol': '₹'},
    ]
    
    for curr_data in currencies_data:
        currency, created = Currency.objects.get_or_create(
            currency_code=curr_data['currency_code'],
            defaults={
                'currency_name': curr_data['currency_name'],
                'symbol': curr_data['symbol'],
                'is_active': True,
                'created_by': superuser
            }
        )
        if created:
            print(f"Created currency: {currency.currency_code}")
    
    # Create Nepali fiscal year 2081-2082 (2024-07-16 to 2025-07-16)
    fiscal_year = FiscalYear.objects.filter(
        organization=organization,
        name="Fiscal Year 2081-2082"
    ).first()
    if not fiscal_year:
        fiscal_year = FiscalYear.objects.create(
            organization=organization,
            name="Fiscal Year 2081-2082",
            start_date=date(2024, 7, 16),
            end_date=date(2025, 7, 16),
            status='open',
            is_current=True,
            is_default=True,
            created_by=superuser
        )
        print(f"Created fiscal year: {fiscal_year.name}")
    else:
        print(f"Using existing fiscal year: {fiscal_year.name}") 
    # Create accounting periods for the Nepali fiscal year
    if created:  # Only create periods if fiscal year was just created
        # Nepali months with their English equivalents and date ranges
        nepali_months = [
            {'nepali': 'Shrawan', 'start': date(2024, 7, 16), 'end': date(2024, 8, 16)},
            {'nepali': 'Bhadra', 'start': date(2024, 8, 17), 'end': date(2024, 9, 16)},
            {'nepali': 'Ashwin', 'start': date(2024, 9, 17), 'end': date(2024, 10, 16)},
            {'nepali': 'Kartik', 'start': date(2024, 10, 17), 'end': date(2024, 11, 15)},
            {'nepali': 'Mangsir', 'start': date(2024, 11, 16), 'end': date(2024, 12, 15)},
            {'nepali': 'Poush', 'start': date(2024, 12, 16), 'end': date(2025, 1, 14)},
            {'nepali': 'Magh', 'start': date(2025, 1, 15), 'end': date(2025, 2, 13)},
            {'nepali': 'Falgun', 'start': date(2025, 2, 14), 'end': date(2025, 3, 15)},
            {'nepali': 'Chaitra', 'start': date(2025, 3, 16), 'end': date(2025, 4, 14)},
            {'nepali': 'Baisakh', 'start': date(2025, 4, 15), 'end': date(2025, 5, 15)},
            {'nepali': 'Jestha', 'start': date(2025, 5, 16), 'end': date(2025, 6, 15)},
            {'nepali': 'Asar', 'start': date(2025, 6, 16), 'end': date(2025, 7, 16)},
        ]
        
        current_nepali_month = 1  # Assuming we're in Shrawan for current period
        
        for i, month_data in enumerate(nepali_months, 1):
            period, period_created = AccountingPeriod.objects.get_or_create(
                fiscal_year=fiscal_year,
                period_number=i,
                defaults={
                    'name': f"{month_data['nepali']} 2081-2082",
                    'start_date': month_data['start'],
                    'end_date': month_data['end'],
                    'status': 'open',
                    'is_current': i == current_nepali_month,
                    'created_by': superuser
                }
            )
            if period_created:
                print(f"Created accounting period: {period.name}")
    
    # Create default departments for Nepal
    departments_data = [
        'Administration',
        'Finance',
        'Human Resources',
        'Information Technology',
        'Operations',
        'Sales & Marketing',
        'Accounts',
        'Audit'
    ]
    
    for dept_name in departments_data:
        code = dept_name[:10].upper().replace(' ', '_')
        department, created = Department.objects.get_or_create(
            organization=organization,
            code=code,
            name=dept_name
        )
        if created:
            print(f"Created department: {department.name}")
    
    # Create default projects
    projects_data = [
        {'name': 'General Operations', 'description': 'General business operations'},
        {'name': 'Infrastructure Development', 'description': 'IT and infrastructure projects'},
        {'name': 'Marketing Campaign', 'description': 'Marketing and promotional activities'},
        {'name': 'Digital Transformation', 'description': 'Digital transformation initiatives'},
    ]
    
    for proj_data in projects_data:
        project, created = Project.objects.get_or_create(
            organization=organization,
            name=proj_data['name'],
            defaults={
                'description': proj_data['description'],
                'is_active': True,
                'start_date': date.today()
            }
        )
        if created:
            print(f"Created project: {project.name}")
    
    # Create default cost centers
    cost_centers_data = [
        {'name': 'Head Office', 'description': 'Main corporate office'},
        {'name': 'Kathmandu Branch', 'description': 'Kathmandu branch office'},
        {'name': 'Pokhara Branch', 'description': 'Pokhara branch office'},
        {'name': 'Manufacturing Unit', 'description': 'Production facility'},
        {'name': 'Research & Development', 'description': 'R&D activities'},
    ]
    
    for cc_data in cost_centers_data:
        code = cc_data['name'][:10].upper().replace(' ', '_')
        cost_center, created = CostCenter.objects.get_or_create(
            name=cc_data['name'],
            organization=organization,
            code=code,
            defaults={
                'description': cc_data['description'],
                'is_active': True
            }
        )
        if created:
            print(f"Created cost center: {cost_center.name}")
    
    # Create default account types
    account_types_data = [
        # Assets
        {'nature': 'asset', 'name': 'Current Assets', 'classification': 'Current', 'balance_sheet_category': 'Current Assets', 'display_order': 1},
        {'nature': 'asset', 'name': 'Fixed Assets', 'classification': 'Non-Current', 'balance_sheet_category': 'Fixed Assets', 'display_order': 2},
        {'nature': 'asset', 'name': 'Intangible Assets', 'classification': 'Non-Current', 'balance_sheet_category': 'Intangible Assets', 'display_order': 3},
        {'nature': 'asset', 'name': 'Investments', 'classification': 'Non-Current', 'balance_sheet_category': 'Investments', 'display_order': 4},
        
        # Liabilities
        {'nature': 'liability', 'name': 'Current Liabilities', 'classification': 'Current', 'balance_sheet_category': 'Current Liabilities', 'display_order': 5},
        {'nature': 'liability', 'name': 'Long-term Liabilities', 'classification': 'Non-Current', 'balance_sheet_category': 'Long-term Liabilities', 'display_order': 6},
        
        # Equity
        {'nature': 'equity', 'name': 'Share Capital', 'classification': 'Equity', 'balance_sheet_category': 'Shareholders Equity', 'display_order': 7},
        {'nature': 'equity', 'name': 'Retained Earnings', 'classification': 'Equity', 'balance_sheet_category': 'Shareholders Equity', 'display_order': 8},
        {'nature': 'equity', 'name': 'Reserves', 'classification': 'Equity', 'balance_sheet_category': 'Shareholders Equity', 'display_order': 9},
        
        # Income
        {'nature': 'income', 'name': 'Revenue', 'classification': 'Operating', 'income_statement_category': 'Revenue', 'display_order': 10},
        {'nature': 'income', 'name': 'Other Income', 'classification': 'Non-Operating', 'income_statement_category': 'Other Income', 'display_order': 11},
        
        # Expenses
        {'nature': 'expense', 'name': 'Cost of Goods Sold', 'classification': 'Direct', 'income_statement_category': 'Cost of Sales', 'display_order': 12},
        {'nature': 'expense', 'name': 'Operating Expenses', 'classification': 'Operating', 'income_statement_category': 'Operating Expenses', 'display_order': 13},
        {'nature': 'expense', 'name': 'Administrative Expenses', 'classification': 'Operating', 'income_statement_category': 'Administrative Expenses', 'display_order': 14},
        {'nature': 'expense', 'name': 'Financial Expenses', 'classification': 'Operating', 'income_statement_category': 'Financial Expenses', 'display_order': 15},
    ]
    
    for acc_type_data in account_types_data:
        account_type, created = AccountType.objects.get_or_create(
            name=acc_type_data['name'],
            nature=acc_type_data['nature'],
            defaults={
                'classification': acc_type_data['classification'],
                'balance_sheet_category': acc_type_data.get('balance_sheet_category'),
                'income_statement_category': acc_type_data.get('income_statement_category'),
                'display_order': acc_type_data['display_order'],
                'system_type': True,
                'created_by': superuser
            }
        )
        if created:
            print(f"Created account type: {account_type.name}")
    
    # Create default chart of accounts for Nepal
    # Get account types for reference
    current_assets = AccountType.objects.get(name='Current Assets')
    fixed_assets = AccountType.objects.get(name='Fixed Assets')
    current_liabilities = AccountType.objects.get(name='Current Liabilities')
    equity = AccountType.objects.get(name='Share Capital')
    revenue = AccountType.objects.get(name='Revenue')
    expenses = AccountType.objects.get(name='Operating Expenses')
    admin_expenses = AccountType.objects.get(name='Administrative Expenses')
    
    accounts_data = [
        # Assets
        {'account_name': 'Cash in Hand', 'account_type': current_assets, 'is_bank_account': False},
        {'account_name': 'Bank Account - NPR', 'account_type': current_assets, 'is_bank_account': True},
        {'account_name': 'Bank Account - USD', 'account_type': current_assets, 'is_bank_account': True},
        {'account_name': 'Accounts Receivable', 'account_type': current_assets, 'is_control_account': True},
        {'account_name': 'Trade Receivables', 'account_type': current_assets},
        {'account_name': 'Inventory - Raw Materials', 'account_type': current_assets},
        {'account_name': 'Inventory - Finished Goods', 'account_type': current_assets},
        {'account_name': 'Prepaid Expenses', 'account_type': current_assets},
        {'account_name': 'Advance to Suppliers', 'account_type': current_assets},
        
        # Fixed Assets
        {'account_name': 'Land and Building', 'account_type': fixed_assets},
        {'account_name': 'Office Equipment', 'account_type': fixed_assets},
        {'account_name': 'Furniture and Fixtures', 'account_type': fixed_assets},
        {'account_name': 'Computer and Software', 'account_type': fixed_assets},
        {'account_name': 'Vehicle', 'account_type': fixed_assets},
        
        # Liabilities
        {'account_name': 'Accounts Payable', 'account_type': current_liabilities, 'is_control_account': True},
        {'account_name': 'Trade Payables', 'account_type': current_liabilities},
        {'account_name': 'VAT Payable', 'account_type': current_liabilities},
        {'account_name': 'TDS Payable', 'account_type': current_liabilities},
        {'account_name': 'Social Security Fund', 'account_type': current_liabilities},
        {'account_name': 'Citizens Investment Trust', 'account_type': current_liabilities},
        {'account_name': 'Provident Fund', 'account_type': current_liabilities},
        {'account_name': 'Salary Payable', 'account_type': current_liabilities},
        {'account_name': 'Accrued Expenses', 'account_type': current_liabilities},
        
        # Equity
        {'account_name': 'Share Capital', 'account_type': equity},
        {'account_name': 'Retained Earnings', 'account_type': equity},
        {'account_name': 'General Reserve', 'account_type': equity},
        
        # Revenue
        {'account_name': 'Sales Revenue', 'account_type': revenue},
        {'account_name': 'Service Revenue', 'account_type': revenue},
        {'account_name': 'Export Revenue', 'account_type': revenue},
        {'account_name': 'Interest Income', 'account_type': revenue},
        {'account_name': 'Other Income', 'account_type': revenue},
        
        # Expenses
        {'account_name': 'Cost of Goods Sold', 'account_type': expenses},
        {'account_name': 'Salary and Wages', 'account_type': admin_expenses},
        {'account_name': 'Office Rent', 'account_type': admin_expenses},
        {'account_name': 'Utilities', 'account_type': admin_expenses},
        {'account_name': 'Office Supplies', 'account_type': admin_expenses},
        {'account_name': 'Professional Fees', 'account_type': admin_expenses},
        {'account_name': 'Travel and Transportation', 'account_type': expenses},
        {'account_name': 'Communication Expenses', 'account_type': admin_expenses},
        {'account_name': 'Depreciation Expense', 'account_type': expenses},
        {'account_name': 'Bank Charges', 'account_type': expenses},
        {'account_name': 'Repair and Maintenance', 'account_type': expenses},
    ]
 
    npr_currency = Currency.objects.get(currency_code='NPR')
    for acc_data in accounts_data:
        # Check for existing account by organization, name, and type
        existing_account = ChartOfAccount.objects.filter(
            organization=organization,
            account_name=acc_data['account_name'],
            account_type=acc_data['account_type'],
            is_bank_account=acc_data.get('is_bank_account', False),
            is_control_account=acc_data.get('is_control_account', False)
        ).first()
        if existing_account:
            print(f"Account already exists: {existing_account.account_name} (type: {existing_account.account_type.name})")
            continue

        # Predict the next account_code that would be generated
        next_code = ChartOfAccount.get_next_code(
            org_id=organization.id,
            parent_id=None,
            account_type_id=acc_data['account_type'].account_type_id
        )
        if ChartOfAccount.objects.filter(organization=organization, account_code=next_code).exists():
            print(f"Account code {next_code} already exists for organization. Skipping account '{acc_data['account_name']}'.")
            continue

        temp_account = ChartOfAccount(
            organization=organization,
            account_name=acc_data['account_name'],
            account_type=acc_data['account_type'],
            description=f"Default {acc_data['account_name']} account",
            is_active=True,
            created_by=superuser,
            currency=npr_currency,
            is_bank_account=acc_data.get('is_bank_account', False),
            is_control_account=acc_data.get('is_control_account', False)
        )
        try:
            temp_account.save()
            print(f"Created account: {temp_account.account_name} (code: {temp_account.account_code})")
        except ValidationError as e:
            print(f"Skipped account '{acc_data['account_name']}': {e}")
            continue
    # Create default journal types
    journal_types_data = [
        {'name': 'General Journal', 'description': 'General journal entries', 'auto_numbering_prefix': 'GJ'},
        {'name': 'Cash Receipt', 'description': 'Cash receipts', 'auto_numbering_prefix': 'CR'},
        {'name': 'Cash Payment', 'description': 'Cash payments', 'auto_numbering_prefix': 'CP'},
        {'name': 'Bank Receipt', 'description': 'Bank receipts', 'auto_numbering_prefix': 'BR'},
        {'name': 'Bank Payment', 'description': 'Bank payments', 'auto_numbering_prefix': 'BP'},
        {'name': 'Sales Journal', 'description': 'Sales transactions', 'auto_numbering_prefix': 'SJ'},
        {'name': 'Purchase Journal', 'description': 'Purchase transactions', 'auto_numbering_prefix': 'PJ'},
        {'name': 'Adjustment Journal', 'description': 'Adjusting entries', 'auto_numbering_prefix': 'AJ'},
    ]
    
    for jt_data in journal_types_data:
        journal_type, created = JournalType.objects.get_or_create(
            organization=organization,
            code=jt_data['auto_numbering_prefix'],  # Use code as unique field
            defaults={
                'name': jt_data['name'],
                'description': jt_data['description'],
                'auto_numbering_prefix': jt_data['auto_numbering_prefix'],
                'auto_numbering_next': 1,
                'is_system_type': True,
                'is_active': True,
                'created_by': superuser
            }
        )
        if created:
            print(f"Created journal type: {journal_type.name}")
        else:
            print(f"Using existing journal type: {journal_type.name}")
    
    # Create default tax authority for Nepal
    tax_authority, created = TaxAuthority.objects.get_or_create(
        organization=organization,
        name='Inland Revenue Department',
        defaults={
            'country_code': 'NP',
            'description': 'Nepal Tax Authority - Inland Revenue Department',
            'is_active': True,
            'is_default': True,
            'created_by': superuser
        }
    )
    if created:
        print(f"Created tax authority: {tax_authority.name}")
    
    # Create default tax types for Nepal
    tax_types_data = [
        {'name': 'Value Added Tax (VAT)', 'filing_frequency': 'monthly'},
        {'name': 'Tax Deducted at Source (TDS)', 'filing_frequency': 'monthly'},
        {'name': 'Income Tax', 'filing_frequency': 'annual'},
    ]
    
    created_tax_types = []
    for tt_data in tax_types_data:
        tax_type, created = TaxType.objects.get_or_create(
            organization=organization,
            name=tt_data['name'],
            defaults={
                'authority': tax_authority,
                'description': f"Nepal {tt_data['name']}",
                'filing_frequency': tt_data['filing_frequency'],
                'is_active': True,
                'created_by': superuser
            }
        )
        if created:
            print(f"Created tax type: {tax_type.name}")
        created_tax_types.append(tax_type)
    
    # Create default tax codes for Nepal
    vat_tax_type = next((tt for tt in created_tax_types if 'VAT' in tt.name), created_tax_types[0])
    tds_tax_type = next((tt for tt in created_tax_types if 'TDS' in tt.name), created_tax_types[0])
    
    tax_codes_data = [
        # VAT Codes
        {'name': 'VAT Standard Rate', 'tax_rate': Decimal('13.00'), 'description': 'Standard VAT rate 13%', 'tax_type': vat_tax_type},
        {'name': 'VAT Zero Rate', 'tax_rate': Decimal('0.00'), 'description': 'Zero VAT rate', 'tax_type': vat_tax_type},
        {'name': 'VAT Exempt', 'tax_rate': Decimal('0.00'), 'description': 'VAT exempt', 'tax_type': vat_tax_type},
        
        # TDS Codes
        {'name': 'TDS Salary', 'tax_rate': Decimal('1.00'), 'description': 'TDS on salary 1%', 'tax_type': tds_tax_type},
        {'name': 'TDS Professional Fee', 'tax_rate': Decimal('5.00'), 'description': 'TDS on professional fees 5%', 'tax_type': tds_tax_type},
        {'name': 'TDS Contractor', 'tax_rate': Decimal('2.00'), 'description': 'TDS on contractor payment 2%', 'tax_type': tds_tax_type},
        {'name': 'TDS Rent', 'tax_rate': Decimal('10.00'), 'description': 'TDS on rent 10%', 'tax_type': tds_tax_type},
    ]
    
    for tc_data in tax_codes_data:
        tax_code, created = TaxCode.objects.get_or_create(
            organization=organization,
            name=tc_data['name'],
            defaults={
                'tax_type': tc_data['tax_type'],
                'tax_authority': tax_authority,
                'tax_rate': tc_data['tax_rate'],
                'rate': tc_data['tax_rate'],
                'description': tc_data['description'],
                'is_active': True,
                'is_recoverable': 'VAT' in tc_data['name'],
                'effective_from': date(2024, 7, 16),  # Start of fiscal year
                'created_by': superuser
            }
        )
        if created:
            print(f"Created tax code: {tax_code.name}")
    
    # Create default voucher mode config
    voucher_config, created = VoucherModeConfig.objects.get_or_create(
        organization=organization,
        name='Nepal Standard Voucher',
        defaults={
            'description': 'Standard voucher configuration for Nepal',
            'is_default': True,
            'layout_style': 'standard',
            'show_account_balances': True,
            'show_tax_details': True,
            'show_dimensions': True,
            'allow_multiple_currencies': True,
            'require_line_description': True,
            'default_currency': 'NPR',
            'created_by': superuser
        }
    )
    if created:
        print(f"Created voucher mode config: {voucher_config.name}")
    
    # --- Default Security Setup: Modules, Entities, Permissions, Roles ---
    # 1. Create default module
    accounting_module, _ = Module.objects.get_or_create(
        name='Accounting',
        code='accounting',
        description='Accounting module',
        icon='fas fa-calculator',
        display_order=1,
        is_active=True
    )
    if not hasattr(accounting_module, 'created_by'):
        pass  # No created_by field to set

    # 2. Create default entities for the module
    entities_data = [
        {'name': 'Fiscal Year', 'code': 'fiscalyear', 'description': 'Fiscal Year management'},
        {'name': 'Accounting Period', 'code': 'accountingperiod', 'description': 'Accounting Period management'},
        {'name': 'Chart of Account', 'code': 'chartofaccount', 'description': 'Chart of Accounts management'},
        {'name': 'Department', 'code': 'department', 'description': 'Department management'},
        {'name': 'Project', 'code': 'project', 'description': 'Project management'},
        {'name': 'Cost Center', 'code': 'costcenter', 'description': 'Cost Center management'},
        {'name': 'Journal Type', 'code': 'journaltype', 'description': 'Journal Type management'},
        {'name': 'Tax Authority', 'code': 'taxauthority', 'description': 'Tax Authority management'},
        {'name': 'Tax Type', 'code': 'taxtype', 'description': 'Tax Type management'},
        {'name': 'Tax Code', 'code': 'taxcode', 'description': 'Tax Code management'},
        {'name': 'Voucher Mode Config', 'code': 'vouchermodeconfig', 'description': 'Voucher Mode Config management'},
    ]
    entity_objs = []
    for ent in entities_data:
        entity, _ = Entity.objects.get_or_create(
            module=accounting_module,
            code=ent['code'],
            defaults={
                'name': ent['name'],
                'description': ent['description'],
                'is_active': True
            }
        )
        entity_objs.append(entity)

    # 3. Create permissions for each entity (CRUD)
    actions = ['view', 'add', 'change', 'delete']
    permission_objs = []
    for entity in entity_objs:
        for action in actions:
            perm, _ = Permission.objects.get_or_create(
                module=accounting_module,
                entity=entity,
                action=action,
                defaults={
                    'name': f'Can {action} {entity.name}',
                    'codename': f'{accounting_module.code}_{entity.code}_{action}',
                    'description': f'Can {action} {entity.name}',
                    'is_active': True
                }
            )
            permission_objs.append(perm)

    # 4. Create roles: Administrator (all permissions), User (view only)
    admin_role, _ = Role.objects.get_or_create(
        name='Administrator',
        code='ADMIN',
        organization=organization,
        defaults={
            'description': 'Full access to all features',
            'is_system': True,
            'is_active': True,
            'created_by': superuser,
            'updated_by': superuser
        }
    )
    user_role, _ = Role.objects.get_or_create(
        name='User',
        code='USER',
        organization=organization,
        defaults={
            'description': 'Basic user access',
            'is_system': True,
            'is_active': True,
            'created_by': superuser,
            'updated_by': superuser
        }
    )
    # Assign permissions
    admin_role.permissions.set(permission_objs)
    admin_role.save()
    view_perms = [p for p in permission_objs if p.action == 'view']
    user_role.permissions.set(view_perms)
    user_role.save()

    # 5. Assign Administrator role to superuser
    UserRole.objects.get_or_create(
        user=superuser,
        role=admin_role,
        organization=organization,
        defaults={
            'is_active': True,
            'created_by': superuser,
            'updated_by': superuser
        }
    )

    print("\nDefault data creation for Nepal completed successfully!")
    print("Summary:")
    print(f"- Organization: {organization.name}")
    print(f"- Fiscal Year: {fiscal_year.name} (2024-07-16 to 2025-07-16)")
    print(f"- Accounting Periods: 12 Nepali months created")
    print(f"- Departments: {len(departments_data)} departments")
    print(f"- Projects: {len(projects_data)} projects")
    print(f"- Cost Centers: {len(cost_centers_data)} cost centers")
    print(f"- Account Types: {len(account_types_data)} account types")
    print(f"- Chart of Accounts: {len(accounts_data)} accounts")
    print(f"- Journal Types: {len(journal_types_data)} journal types")
    print(f"- Tax Codes: {len(tax_codes_data)} tax codes")
    print(f"- Currencies: {len(currencies_data)} currencies (NPR as default)")
    print(f"- Tax Authority: Inland Revenue Department")
    print(f"- Default Currency: NPR (Nepalese Rupee)")

if __name__ == '__main__':
    create_default_data()