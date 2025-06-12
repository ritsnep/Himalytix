# urls.py
from django.urls import path
from . import views

app_name = "accounting"
urlpatterns = [
    # Journal URLs
    path('journals/', views.JournalListView.as_view(), name='journal_list'),
    path('journals/create/', views.JournalCreateView.as_view(), name='journal_create'),
    path('journals/<int:pk>/', views.JournalDetailView.as_view(), name='journal_detail'),
    path('journals/<int:pk>/edit/', views.JournalUpdateView.as_view(), name='journal_update'),
    path('journals/<int:pk>/post/', views.JournalPostView.as_view(), name='journal_post'),
    
    # HTMX Partial URLs
    path('htmx/journal-line-form/', views.HTMXJournalLineFormView.as_view(), name='htmx_journal_line_form'),
    path('htmx/account-autocomplete/', views.HTMXAccountAutocompleteView.as_view(), name='htmx_account_autocomplete'),
    
    # Voucher Mode URLs
    path('voucher-configs/', views.VoucherModeConfigListView.as_view(), name='voucher_config_list'),
    path('voucher-configs/create/', views.VoucherModeConfigCreateView.as_view(), name='voucher_config_create'),
    path('voucher-configs/<int:pk>/', views.VoucherModeConfigDetailView.as_view(), name='voucher_config_detail'),
    path('voucher-configs/<int:pk>/edit/', views.VoucherModeConfigUpdateView.as_view(), name='voucher_config_update'),
    
    path('voucher-config/<int:type_id>.hx/', views.VoucherConfigHXView.as_view(), name='voucher_config_hx'),
    
    path('voucher-configs/<int:config_id>/defaults/create/', views.VoucherModeDefaultCreateView.as_view(), name='voucher_default_create'),
    path('voucher-defaults/<int:pk>/edit/', views.VoucherModeDefaultUpdateView.as_view(), name='voucher_default_update'),
    path('voucher-defaults/<int:pk>/delete/', views.VoucherModeDefaultDeleteView.as_view(), name='voucher_default_delete'),
    
    path('voucher-entry/', views.VoucherEntryView.as_view(), name='voucher_entry'),
    path('voucher-entry/<int:config_id>/', views.VoucherEntryView.as_view(), name='voucher_entry_config'),
    
    # Fiscal Year URLs
    path('fiscal_year/', views.FiscalYearCreateView.as_view(), name='fiscal_year_create'),
    path('fiscal_year/list/', views.FiscalYearListView.as_view(), name='fiscal_year_list'),
    path('fiscal_year/<str:fiscal_year_id>/', views.FiscalYearUpdateView.as_view(), name='fiscal_year_update'),
    
    # Cost Center URLs
    path('cost-centers/', views.CostCenterListView.as_view(), name='costcenter_list'),
    path('cost-centers/create/', views.CostCenterCreateView.as_view(), name='costcenter_create'),
    path('cost-centers/<int:pk>/edit/', views.CostCenterUpdateView.as_view(), name='costcenter_update'),

    # Department URLs
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/update/', views.DepartmentUpdateView.as_view(), name='department_update'),
    # path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),

    # Chart of Accounts URLs
    path('chart-of-accounts/', views.ChartOfAccountListView.as_view(), name='chart_of_accounts_list'),    
    path('chart-of-accounts.hx/', views.ChartOfAccountListPartial.as_view(), name='chart_of_accounts_list_hx'),
    path('chart-of-accounts/create/', views.ChartOfAccountCreateView.as_view(), name='chart_of_accounts_create'),
    path('chart-of-accounts/<int:pk>/update/', views.ChartOfAccountUpdateView.as_view(), name='chart_of_accounts_update'),
    # path('chart-of-accounts/<int:pk>/delete/', views.ChartOfAccountDeleteView.as_view(), name='chart_of_accounts_delete'),

    # Account Type URLs
    path('account-types/', views.AccountTypeListView.as_view(), name='account_type_list'),
    path('account-types/create/', views.AccountTypeCreateView.as_view(), name='account_type_create'),
    path('account-types/<int:pk>/edit/', views.AccountTypeUpdateView.as_view(), name='account_type_update'),

    # Currency URLs
    path('currencies/', views.CurrencyListView.as_view(), name='currency_list'),
    path('currencies/create/', views.CurrencyCreateView.as_view(), name='currency_create'),
    path('currencies/<str:currency_code>/edit/', views.CurrencyUpdateView.as_view(), name='currency_update'),

    # Currency Exchange Rate URLs
    path('exchange-rates/', views.CurrencyExchangeRateListView.as_view(), name='exchange_rate_list'),
    path('exchange-rates/create/', views.CurrencyExchangeRateCreateView.as_view(), name='exchange_rate_create'),
    path('exchange-rates/<int:pk>/edit/', views.CurrencyExchangeRateUpdateView.as_view(), name='exchange_rate_update'),

    # Tax Authority URLs
    path('tax-authorities/', views.TaxAuthorityListView.as_view(), name='tax_authority_list'),
    path('tax-authorities/create/', views.TaxAuthorityCreateView.as_view(), name='tax_authority_create'),
    path('tax-authorities/<int:pk>/edit/', views.TaxAuthorityUpdateView.as_view(), name='tax_authority_update'),

    # Tax Type URLs
    path('tax-types/', views.TaxTypeListView.as_view(), name='tax_type_list'),
    path('tax-types/create/', views.TaxTypeCreateView.as_view(), name='tax_type_create'),
    path('tax-types/<int:pk>/edit/', views.TaxTypeUpdateView.as_view(), name='tax_type_update'),

    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
]