from .models import (
    FiscalYear, GeneralLedger, Journal, JournalLine, JournalType, ChartOfAccount, 
    AccountingPeriod, TaxCode, Department, Project, CostCenter,
    VoucherModeConfig, VoucherModeDefault, Currency, CurrencyExchangeRate, TaxAuthority, TaxType
)
from .forms import *
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .views_mixins import UserOrganizationMixin, PermissionRequiredMixin
from django.urls import reverse
from usermanagement.utils import PermissionUtils  # Add this import for PermissionUtils
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models

class FiscalYearListView(LoginRequiredMixin, UserOrganizationMixin, ListView):
    model = FiscalYear
    template_name = 'accounting/fiscal_year_list.html'
    context_object_name = 'fiscal_years'
    paginate_by = 20

    def get_queryset(self):
        org = self.get_organization()
        if not org:
            return self.model.objects.none()
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = user.get_active_organization()
        if not org:
            context['can_add'] = False
            context['can_change'] = False
            context['can_delete'] = False
        else:
            context['can_add'] = PermissionUtils.has_permission(user, org, 'accounting', 'fiscalyear', 'add')
            context['can_change'] = PermissionUtils.has_permission(user, org, 'accounting', 'fiscalyear', 'change')
            context['can_delete'] = PermissionUtils.has_permission(user, org, 'accounting', 'fiscalyear', 'delete')
        
        context['create_url'] = reverse('accounting:fiscal_year_create')
        context['create_button_text'] = 'New Fiscal Year'
        context['page_title'] = 'Fiscal Years'
        return context

class CostCenterListView(LoginRequiredMixin, ListView):
    model = CostCenter
    template_name = 'accounting/costcenter_list.html'
    context_object_name = 'cost_centers'
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        return CostCenter.objects.filter(
            organization_id=self.request.user.organization,
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=today),
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:costcenter_create')
        context['create_button_text'] = 'New Cost Center'
        context['page_title'] = 'Cost Centers'
        context['breadcrumbs'] = [
            ('Cost Centers', None),
        ]
        return context


class JournalListView(LoginRequiredMixin, ListView):
    model = Journal
    template_name = 'accounting/journal_list.html'
    context_object_name = 'journals'
    paginate_by = 20

    def get_queryset(self):
        return Journal.objects.filter(organization=self.request.user.organization).order_by('-journal_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:journal_create')
        context['create_button_text'] = 'New Journal'
        context['page_title'] = 'Journals'
        context['breadcrumbs'] = [
            ('Journals', None),
        ]
        return context

class VoucherModeConfigListView(LoginRequiredMixin, ListView):
    model = VoucherModeConfig
    template_name = 'accounting/voucher_config_list.html'
    context_object_name = 'configs'
    
    def get_queryset(self):
        return VoucherModeConfig.objects.filter(organization=self.request.user.organization)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:voucher_config_create')
        context['create_button_text'] = 'New Voucher Mode Config'
        context['page_title'] = 'Voucher Configurations'
        context['breadcrumbs'] = [
            ('Voucher Configurations', None),
        ]
        return context


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'accounting/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        today = timezone.now().date()
        return Department.objects.filter(
            organization=self.request.user.organization,
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=today),
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:department_create')
        context['create_button_text'] = 'New Department'
        context['page_title'] = 'Departments'
        context['breadcrumbs'] = [
            ('Departments', None),
        ]
        return context


class ChartOfAccountListView(LoginRequiredMixin, ListView):
    model = ChartOfAccount
    template_name = 'accounting/chart_of_accounts_list.html'
    context_object_name = 'accounts'
    paginate_by = 20
    
    def get_queryset(self):
        return ChartOfAccount.objects.filter(
            organization=self.request.user.organization
        ).order_by('account_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:chart_of_accounts_create')
        context['create_button_text'] = 'New Chart of Account'
        context['page_title'] = 'Chart of Accounts'
        context['breadcrumbs'] = [
            ('Chart of Accounts', None),
        ]
        return context
    
class CurrencyListView(LoginRequiredMixin, ListView):
    model = Currency
    template_name = 'accounting/currency_list.html'
    context_object_name = 'currencies'
    paginate_by = 20

    def get_queryset(self):
        return Currency.objects.all().order_by('currency_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:currency_create')
        context['create_button_text'] = 'New Currency'
        context['page_title'] = 'Currencies'
        context['breadcrumbs'] = [
            ('Currencies', None),
        ]
        return context

class CurrencyExchangeRateListView(LoginRequiredMixin, ListView):
    model = CurrencyExchangeRate
    template_name = 'accounting/currency_exchange_rate_list.html'
    context_object_name = 'exchange_rates'
    paginate_by = 20

    def get_queryset(self):
        return CurrencyExchangeRate.objects.filter(
            organization=self.request.user.organization
        ).select_related('from_currency', 'to_currency').order_by('-rate_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Exchange Rates'
        context['create_url'] = reverse('accounting:exchange_rate_create')
        context['create_button_text'] = 'New Exchange Rate'
        context['breadcrumbs'] = [
            ('Exchange Rates', None),
        ]
        return context


class TaxAuthorityListView(LoginRequiredMixin, ListView):
    model = TaxAuthority
    template_name = 'accounting/tax_authority_list.html'
    context_object_name = 'tax_authorities'
    paginate_by = 20

    def get_queryset(self):
        return TaxAuthority.objects.filter(
            organization=self.request.user.organization
        ).order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:tax_authority_create')
        context['create_button_text'] = 'New Tax Authority'
        context['page_title'] = 'Tax Authorities'
        context['breadcrumbs'] = [
            ('Tax Authorities', None),
        ]
        return context


class TaxTypeListView(LoginRequiredMixin, ListView):
    model = TaxType
    template_name = 'accounting/tax_type_list.html'
    context_object_name = 'tax_types'
    paginate_by = 20

    def get_queryset(self):
        return TaxType.objects.filter(
            organization=self.request.user.organization
        ).order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:tax_type_create')
        context['create_button_text'] = 'New Tax Type'
        context['page_title'] = 'Tax Types'
        context['breadcrumbs'] = [
            ('Tax Types', None),
        ]
        return context


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'accounting/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        return Project.objects.filter(
            organization=self.request.user.organization,
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=today),
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        ).order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:project_create')
        context['create_button_text'] = 'New Project'
        context['page_title'] = 'Projects'
        context['breadcrumbs'] = [
            ('Projects', None),
        ]
        return context


class AccountingPeriodListView(LoginRequiredMixin, UserOrganizationMixin, ListView):
    model = AccountingPeriod
    template_name = 'accounting/accounting_period_list.html'
    context_object_name = 'accounting_periods'
    paginate_by = 20

    def get_queryset(self):
        org = self.get_organization()
        if not org:
            return self.model.objects.none()
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = user.get_active_organization()
        context['create_url'] = reverse('accounting:accounting_period_create')
        context['create_button_text'] = 'New Accounting Period'
        context['page_title'] = 'Accounting Periods'
        return context

class JournalTypeListView(LoginRequiredMixin, UserOrganizationMixin, ListView):
    model = JournalType
    template_name = 'accounting/journal_type_list.html'
    context_object_name = 'journal_types'
    paginate_by = 20
    queryset = JournalType.objects.order_by('name')
   
    def get_queryset(self):
        org = self.get_organization()
        if not org:
            return self.model.objects.none()
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = user.get_active_organization()
        context['create_url'] = reverse('accounting:journal_type_create')
        context['create_button_text'] = 'New Journal Type'
        context['page_title'] = 'Journal Types'
        return context

class JournalDetailView(LoginRequiredMixin, DetailView):
    model = Journal
    template_name = 'accounting/journal_detail.html'
    context_object_name = 'journal'

class JournalPostView(LoginRequiredMixin, View):
    def post(self, request, pk):
        journal = get_object_or_404(Journal, pk=pk, organization=request.user.organization)
        if journal.status != 'draft':
            return JsonResponse({'success': False, 'error': 'Journal is not in draft status'})
        with transaction.atomic():
            for line in journal.lines.all():
                GeneralLedger.objects.create(
                    organization=journal.organization,
                    account=line.account,
                    journal=journal,
                    journal_line=line,
                    period=journal.period,
                    transaction_date=journal.journal_date,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    balance_after=line.account.current_balance + (line.debit_amount - line.credit_amount),
                    currency_code=line.currency_code,
                    exchange_rate=line.exchange_rate,
                    functional_debit_amount=line.functional_debit_amount,
                    functional_credit_amount=line.functional_credit_amount,
                    department=line.department,
                    project=line.project,
                    cost_center=line.cost_center,
                    description=line.description,
                    source_module=journal.source_module,
                    source_reference=journal.source_reference,
                )
                line.account.current_balance += (line.debit_amount - line.credit_amount)
                line.account.save()
            journal.status = 'posted'
            journal.posted_at = timezone.now()
            journal.posted_by = request.user
            journal.save()
        return JsonResponse({'success': True})