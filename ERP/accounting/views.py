from asyncio.log import logger
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView,  UpdateView, DetailView, TemplateView, CreateView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseForbidden, HttpResponseServerError, JsonResponse, HttpResponse
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import AccountType, Currency, CurrencyExchangeRate, FiscalYear, TaxAuthority, TaxType
from .forms import AccountTypeForm, ChartOfAccountForm, CostCenterForm, CurrencyExchangeRateForm, CurrencyForm, DepartmentForm, FiscalYearForm, ProjectForm, TaxAuthorityForm, TaxTypeForm
from django.contrib import messages
from django.db.models import F
from django.http import JsonResponse
from .models import ChartOfAccount  # adjust as needed

from .serializers import VoucherModeConfigSerializer

from .models import (
    FiscalYear, GeneralLedger, Journal, JournalLine, JournalType, ChartOfAccount, 
    AccountingPeriod, TaxCode, Department, Project, CostCenter,
    VoucherModeConfig, VoucherModeDefault, VoucherUDFConfig
)
from .forms import (
    JournalForm, JournalLineForm, JournalLineFormSet,
    VoucherModeConfigForm, VoucherModeDefaultForm, VoucherUDFConfigForm, AccountingPeriodForm, JournalTypeForm
)


from django.urls import reverse_lazy
from utils.htmx import require_htmx
from usermanagement.utils import require_permission
from usermanagement.utils import PermissionUtils
from django.forms import inlineformset_factory
from .views_mixins import UserOrganizationMixin, PermissionRequiredMixin, VoucherConfigMixin
from .views_list import *
from .views_create import *
from .views_update import *
from .views_delete import *
from .forms import ChartOfAccountForm
from django.views.decorators.csrf import csrf_exempt
from utils.form_restore import get_pending_form_initial, clear_pending_form
from django.db.models import Prefetch
import logging
from decimal import Decimal
from django.db.models import Sum
from .forms_factory import build_form
from django.forms import formset_factory

logger = logging.getLogger(__name__)

class HTMXAccountAutocompleteView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('query', '')
        accounts = ChartOfAccount.objects.filter(
            organization_id=request.user.get_active_organization().id,
            account_code__icontains=query
        )[:10]
        results = [{'id': a.account_id, 'text': f"{a.account_code} - {a.account_name}"} for a in accounts]
        return JsonResponse({'results': results})

class HTMXJournalLineFormView(LoginRequiredMixin, View):
    def get(self, request):
        organization = request.user.get_active_organization()
        form_index = request.GET.get('index', '0') # Get the index for the new form

        # Create a single empty form from the formset
        form = JournalLineForm(prefix=f'lines-{form_index}', organization=organization)

        # Manually set required attributes for new form for client-side validation
        # These are set in the forms.py now, but can be reinforced here if needed
        # form.fields['account'].widget.attrs['required'] = 'required'
        # form.fields['debit_amount'].widget.attrs['required'] = 'required'
        # form.fields['credit_amount'].widget.attrs['required'] = 'required'

        return render(request, 'accounting/partials/journal_line_form.html', {'form': form})

# Voucher Mode Views
class VoucherModeConfigListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = VoucherModeConfig
    template_name = 'accounting/voucher_config_list.html'
    context_object_name = 'configs'
    permission_required = ('accounting', 'vouchermodeconfig', 'view')
    
    def get_queryset(self):
        return VoucherModeConfig.objects.filter(organization_id=self.request.user.get_active_organization().id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:voucher_config_create')
        context['create_button_text'] = 'New Voucher Mode Config'
        context['page_title'] = 'Voucher Configurations'
        context['breadcrumbs'] = [
            ('Voucher Configurations', None),
        ]
        return context

class VoucherModeConfigUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VoucherModeConfig
    form_class = VoucherModeConfigForm
    template_name = 'accounting/voucher_config_form.html'
    permission_required = ('accounting', 'vouchermodeconfig', 'change')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Voucher configuration updated successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': f'Update Voucher Configuration: {self.object.name}',
            'page_title': f'Update Voucher Configuration: {self.object.name}',
            'breadcrumbs': [
                ('Voucher Configurations', reverse('accounting:voucher_config_list')),
                (f'Update {self.object.name}', None)
            ]
        })
        return context

class VoucherModeConfigDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = VoucherModeConfig
    template_name = 'accounting/voucher_config_detail.html'
    context_object_name = 'config'
    permission_required = ('accounting', 'vouchermodeconfig', 'view')

    def get_queryset(self):
        return VoucherModeConfig.objects.filter(organization_id=self.request.user.get_active_organization().id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': f'Voucher Configuration Details: {self.object.name}',
            'page_title': f'Voucher Configuration Details: {self.object.name}',
            'breadcrumbs': [
                ('Voucher Configurations', reverse('accounting:voucher_config_list')),
                (f'Details: {self.object.name}', None)
            ]
        })
        return context

class VoucherConfigHXView(LoginRequiredMixin, View):
    """Return voucher configuration fragment and layout JSON."""

    def get(self, request, type_id: int):
        org = request.user.get_active_organization()
        config = get_object_or_404(VoucherModeConfig, organization_id=org.id, journal_type_id=type_id)
        layout_cfg = VoucherModeConfigSerializer(config).data
        html = render(request, 'accounting/voucher_fragment.html', {
            'layout_cfg': json.dumps(layout_cfg)
        }).content.decode('utf-8')
        return HttpResponse(html)

class VoucherModeDefaultUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VoucherModeDefault
    form_class = VoucherModeDefaultForm
    template_name = 'accounting/voucher_default_form.html'
    permission_required = ('accounting', 'vouchermodedefault', 'change')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        kwargs['config_id'] = self.object.config_id
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': self.object.config_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = get_object_or_404(VoucherModeConfig, pk=self.object.config_id, organization_id=self.request.user.get_active_organization().id)
        context.update({
            'form_title': f'Update Default Line for {config.name}',
            'page_title': f'Update Default Line: {config.name}',
            'breadcrumbs': [
                ('Voucher Configurations', reverse('accounting:voucher_config_list')),
                (f'{config.name} Details', reverse('accounting:voucher_config_detail', kwargs={'pk': config.pk})),
                ('Update Default Line', None)
            ]
        })
        return context

class VoucherModeDefaultDeleteView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = ('accounting', 'vouchermodedefault', 'delete')
    
    def post(self, request, pk):
        default = get_object_or_404(VoucherModeDefault, pk=pk, config__organization_id=request.user.get_active_organization().id)
        config_id = default.config_id
        default.delete()
        messages.success(request, "Voucher default line deleted successfully.")
        return redirect(reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': config_id}))

class VoucherEntryView(VoucherConfigMixin, PermissionRequiredMixin, LoginRequiredMixin, View):
    template_name = 'accounting/voucher_entry.html'
    permission_required = ('accounting', 'journal', 'add')
    config_pk_kwarg = "config_id"

    def get_user_perms(self, request):
        return {
            "can_edit": request.user.has_perm("accounting.change_journal"),
            "can_add": request.user.has_perm("accounting.add_journal"),
            "can_delete": request.user.has_perm("accounting.delete_journal"),
        }

    def get(self, request, *args, **kwargs):
        config = self.get_config()
        ui_schema = config.ui_schema or {}
        organization = request.user.get_active_organization()
        HeaderForm = build_form(ui_schema.get("header", {}), organization=organization, prefix="header", model=Journal)
        header_form = HeaderForm()
        LineForm = build_form(ui_schema.get("lines", {}), organization=organization, prefix="line", model=JournalLine)
        LineFormSet = formset_factory(LineForm, extra=2, can_delete=True)
        line_formset = LineFormSet()
        user_perms = self.get_user_perms(request)
        # Pass UDFs to template
        context = {
            "config": config,
            "header_form": header_form,
            "line_formset": line_formset,
            "user_perms": user_perms,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        config = self.get_config()
        ui_schema = config.ui_schema or {}
        organization = request.user.get_active_organization()
        HeaderForm = build_form(ui_schema.get("header", {}), organization=organization, prefix="header", model=Journal)
        header_form = HeaderForm(request.POST)
        LineForm = build_form(ui_schema.get("lines", {}), organization=organization, prefix="line", model=JournalLine)
        LineFormSet = formset_factory(LineForm, can_delete=True)
        line_formset = LineFormSet(request.POST)
        user_perms = self.get_user_perms(request)

        if header_form.is_valid() and line_formset.is_valid():
            header_data = header_form.cleaned_data
            lines_data = [f.cleaned_data for f in line_formset.forms if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
            # Extract UDFs
            udf_header = {}
            udf_lines = []
            for udf in config.udf_configs.all():
                if udf.scope == 'header':
                    udf_header[udf.field_name] = request.POST.get(f'udf_{udf.field_name}')
                elif udf.scope == 'line':
                    udf_line_values = []
                    for i, form in enumerate(line_formset.forms):
                        udf_line_values.append(request.POST.get(f'udf_{udf.field_name}_{i}'))
                    udf_lines.append({udf.field_name: udf_line_values})
            # Pass UDFs to create_voucher or save as needed
            from .services import create_voucher
            journal = create_voucher(
                user=request.user,
                config_id=config.pk,
                header_data=header_data,
                lines_data=lines_data,
                udf_header=udf_header,
                udf_lines=udf_lines,
            )
            messages.success(request, "Voucher created successfully.")
            return redirect('accounting:voucher_entry')  # Or wherever you want to redirect

        context = {
            "config": config,
            "header_form": header_form,
            "line_formset": line_formset,
            "user_perms": user_perms,
        }
        return render(request, self.template_name, context)

class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'accounting/department_list.html'
    context_object_name = 'departments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:department_create')
        context['create_button_text'] = 'New Department'
        context['page_title'] = 'Departments'
        context['breadcrumbs'] = [
            ('Departments', None),
        ]
        return context


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'accounting/department_form.html'
    success_url = reverse_lazy('accounting:department_list')
    
    def get_queryset(self):
        return Department.objects.all()
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Department'
        context['back_url'] = reverse('accounting:department_list')
        context['breadcrumbs'] = [
            ('Departments', reverse('accounting:department_list')),
            ('Update Department', None)
        ]
        return context

# Chart of Accounts Views
class ChartOfAccountListView(LoginRequiredMixin, ListView):
    model = ChartOfAccount
    template_name = 'accounting/chart_of_accounts_list.html'
    context_object_name = 'accounts'
    paginate_by = None  # Show all for tree

    def get_queryset(self):
        # Prefetch parent_account and account_type to avoid N+1
        return ChartOfAccount.objects.filter(
            organization_id=self.request.user.organization.id
        ).select_related('parent_account', 'account_type').order_by('account_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = list(self.get_queryset())
        # Build a tree structure
        tree = []
        id_map = {}
        for acc in accounts:
            acc.children = []
            acc.level = 0
            acc.indent_px = 0
            id_map[acc.account_id] = acc
        for acc in accounts:
            if acc.parent_account_id:
                parent = id_map.get(acc.parent_account_id)
                if parent:
                    acc.level = parent.level + 1
                    acc.indent_px = int(acc.level) * 20  # Ensure integer
                    parent.children.append(acc)
            else:
                acc.level = 0
                acc.indent_px = 0
                tree.append(acc)
        # Ensure children are lists, not querysets
        for acc in accounts:
            if not isinstance(acc.children, list):
                acc.children = list(acc.children)
        context['account_tree'] = tree
        context['create_url'] = reverse('accounting:chart_of_accounts_create')
        context['create_button_text'] = 'New Chart of Account'
        context['page_title'] = 'Chart of Accounts'
        context['breadcrumbs'] = [
            ('Chart of Accounts', None),
        ]
        # Remove columns/data/actions for table_tree.html
        # context['columns'] = ...
        # context['data'] = ...
        # context['actions'] = ...
        # Pass level=0 for the root include
        context['level'] = 0
        return context
    
class ChartOfAccountListPartial(ChartOfAccountListView):
    """HTMX partial for chart of accounts list."""
    template_name = "accounting/chart_of_accounts_list_partial.html"

    @method_decorator(require_htmx)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class ChartOfAccountUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ChartOfAccount
    form_class = ChartOfAccountForm
    template_name = 'accounting/chart_of_accounts_form.html'
    success_url = reverse_lazy('accounting:chart_of_accounts_list')
    permission_required = ('accounting', 'chartofaccount', 'change')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_queryset(self):
        return ChartOfAccount.objects.filter(organization_id=self.request.user.organization.id)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.instance.updated_by = self.request.user
                
                # Save the form
                response = super().form_valid(form)
                
                # If it's an HTMX request, return a success message
                if self.request.headers.get('HX-Request'):
                    messages.success(self.request, "Chart of Account updated successfully.")
                    return HttpResponse(
                        '<div class="alert alert-success">Chart of Account updated successfully.</div>',
                        status=200
                    )
                
                messages.success(self.request, "Chart of Account updated successfully.")
                return response
                
        except Exception as e:
            logger.error(f"Error updating chart of account: {str(e)}")
            if self.request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="alert alert-danger">Error updating Chart of Account: {str(e)}</div>',
                    status=400
                )
            messages.error(self.request, f"Error updating Chart of Account: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                f'<div class="alert alert-danger">{" ".join([str(error) for error in form.non_field_errors()])}</div>',
                status=400
            )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Chart of Account'
        context['back_url'] = reverse('accounting:chart_of_accounts_list')
        context['breadcrumbs'] = [
            ('Chart of Accounts', reverse('accounting:chart_of_accounts_list')),
            ('Edit Chart of Account', None)
        ]
        # Set the correct post URL for the form
        context['form_post_url'] = reverse('accounting:chart_of_accounts_update', kwargs={'pk': self.object.pk})
        return context

    def handle_no_permission(self):
        logger.warning(f"User {self.request.user} denied permission to update ChartOfAccount {self.get_object().pk if self.get_object() else ''}")
        return super().handle_no_permission()

class ChartOfAccountDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ChartOfAccount
    template_name = 'accounting/chart_of_accounts_confirm_delete.html'
    success_url = reverse_lazy('accounting:chart_of_accounts_list')
    permission_required = ('accounting', 'chartofaccount', 'delete')

    def get_queryset(self):
        return ChartOfAccount.objects.filter(organization_id=self.request.user.organization.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['form_title'] = 'Delete Chart of Account'
        context['page_title'] = 'Delete Chart of Account'
        context['breadcrumbs'] = [
            ('Chart of Accounts', reverse_lazy('accounting:chart_of_accounts_list')),
            (f'Delete: {obj.account_code} - {obj.account_name}', None)
        ]
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if ChartOfAccount.objects.filter(parent_account_id=self.object.pk).exists():
            messages.error(request, "Cannot delete an account that has sub-accounts. Please remove or reassign its children first.")
            return redirect(self.success_url)
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        logger.warning(f"User {self.request.user} denied permission to delete ChartOfAccount {self.get_object().pk if self.get_object() else ''}")
        return super().handle_no_permission()

# Account Type Views
class AccountTypeListView(LoginRequiredMixin, ListView):
    model = AccountType
    template_name = 'accounting/account_type_list.html'
    context_object_name = 'account_types'
    paginate_by = 20

    def get_queryset(self):
        return AccountType.objects.all().order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:account_type_create')
        context['create_button_text'] = 'New Account Type'
        context['page_title'] = 'Account Types'
        context['breadcrumbs'] = [
            ('Account Types', None),
        ]
        return context

 

class AccountTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = AccountType
    form_class = AccountTypeForm
    template_name = 'accounting/account_type_form.html'
    success_url = reverse_lazy('accounting:account_type_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Account Type'
        context['back_url'] = reverse('accounting:account_type_list')
        context['breadcrumbs'] = [
            ('Account Types', reverse('accounting:account_type_list')),
            ('Update Account Type', None)
        ]
        return context

# Currency Views
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
 
class CurrencyUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'accounting/currency_form.html'
    success_url = reverse_lazy('accounting:currency_list')
    permission_required = ('accounting', 'currency', 'change')
    pk_url_kwarg = 'currency_code'

    def get_object(self, queryset=None):
        return get_object_or_404(Currency, currency_code=self.kwargs['currency_code'])

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Currency'
        context['back_url'] = reverse('accounting:currency_list')
        context['breadcrumbs'] = [
            ('Currencies', reverse('accounting:currency_list')),
            ('Update Currency', None)
        ]
        return context

# Currency Exchange Rate Views
class CurrencyExchangeRateListView(LoginRequiredMixin, ListView):
    model = CurrencyExchangeRate
    template_name = 'accounting/currency_exchange_rate_list.html'
    context_object_name = 'exchange_rates'
    paginate_by = 20

    def get_queryset(self):
        return CurrencyExchangeRate.objects.filter(
            organization_id=self.request.user.organization.id
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
 

class CurrencyExchangeRateUpdateView(LoginRequiredMixin, UpdateView):
    model = CurrencyExchangeRate
    form_class = CurrencyExchangeRateForm
    template_name = 'accounting/currency_exchange_rate_form.html'
    success_url = reverse_lazy('accounting:exchange_rate_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Exchange Rate'
        context['back_url'] = reverse('accounting:exchange_rate_list')
        context['breadcrumbs'] = [
            ('Exchange Rates', reverse('accounting:exchange_rate_list')),
            ('Update Exchange Rate', None)
        ]
        return context

# Tax Authority Views
class TaxAuthorityListView(LoginRequiredMixin, ListView):
    model = TaxAuthority
    template_name = 'accounting/tax_authority_list.html'
    context_object_name = 'tax_authorities'
    paginate_by = 20

    def get_queryset(self):
        return TaxAuthority.objects.filter(
            organization_id=self.request.user.organization.id
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


class TaxAuthorityUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxAuthority
    form_class = TaxAuthorityForm
    template_name = 'accounting/tax_authority_form.html'
    success_url = reverse_lazy('accounting:tax_authority_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_queryset(self):
        return TaxAuthority.objects.filter(organization_id=self.request.user.organization.id)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Tax Authority'
        context['back_url'] = reverse('accounting:tax_authority_list')
        context['breadcrumbs'] = [
            ('Tax Authorities', reverse('accounting:tax_authority_list')),
            ('Update Tax Authority', None)
        ]
        return context

# Tax Type Views
class TaxTypeListView(LoginRequiredMixin, ListView):
    model = TaxType
    template_name = 'accounting/tax_type_list.html'
    context_object_name = 'tax_types'
    paginate_by = 20

    def get_queryset(self):
        return TaxType.objects.filter(
            organization_id=self.request.user.organization.id
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


class TaxTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = 'accounting/tax_type_form.html'
    success_url = reverse_lazy('accounting:tax_type_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_queryset(self):
        return TaxType.objects.filter(organization_id=self.request.user.organization.id)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Tax Type'
        context['back_url'] = reverse('accounting:tax_type_list')
        context['breadcrumbs'] = [
            ('Tax Types', reverse('accounting:tax_type_list')),
            ('Update Tax Type', None)
        ]
        return context

# Project Views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'accounting/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        return Project.objects.filter(
            organization_id=self.request.user.organization.id
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



class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'accounting/project_form.html'
    success_url = reverse_lazy('accounting:project_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_queryset(self):
        return Project.objects.filter(organization_id=self.request.user.organization.id)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Project'
        context['back_url'] = reverse('accounting:project_list')
        context['breadcrumbs'] = [
            ('Projects', reverse('accounting:project_list')),
            ('Update Project', None)
        ]
        return context

# Accounting Period Views
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


class AccountingPeriodUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, UpdateView):
    model = AccountingPeriod
    form_class = AccountingPeriodForm
    template_name = 'accounting/accounting_period_form.html'
    success_url = reverse_lazy('accounting:accounting_period_list')
    permission_required = ('accounting', 'accountingperiod', 'change')
    slug_field = 'period_id'
    slug_url_kwarg = 'period_id'

    def get_queryset(self):
        return super().get_queryset()

    def get_object(self, queryset=None):
        return get_object_or_404(
            AccountingPeriod,
            period_id=self.kwargs['period_id'],
            fiscal_year__organization_id=self.request.user.get_active_organization().id
        )

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Accounting Period'
        context['back_url'] = reverse('accounting:accounting_period_list')
        return context

class AccountingPeriodDetailView(LoginRequiredMixin, UserOrganizationMixin, DetailView):
    model = AccountingPeriod
    template_name = 'accounting/accounting_period_detail.html'
    context_object_name = 'accounting_period'
    slug_field = 'period_id'
    slug_url_kwarg = 'period_id'

    def get_queryset(self):
        return super().get_queryset()

# Journal Type Views
class JournalTypeListView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, ListView):
    model = JournalType
    template_name = 'accounting/journal_type_list.html'
    context_object_name = 'journal_types'
    paginate_by = 20
    permission_required = ('accounting', 'journaltype', 'view')
   
    def get_queryset(self):
        org = self.get_organization()
        if not org:
            return self.model.objects.none()
        return JournalType.objects.filter(organization=org).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:journal_type_create')
        context['create_button_text'] = 'New Journal Type'
        context['page_title'] = 'Journal Types'
        context['breadcrumbs'] = [
            ('Journal Types', None),
        ]
        return context


class JournalTypeUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, UpdateView):
    model = JournalType
    form_class = JournalTypeForm
    template_name = 'accounting/journal_type_form.html'
    success_url = reverse_lazy('accounting:journal_type_list')
    permission_required = ('accounting', 'journaltype', 'change')
    slug_field = 'journal_type_id'
    slug_url_kwarg = 'journal_type_id'

    def get_queryset(self):
        return JournalType.objects.filter(organization=self.get_organization())

    def get_object(self, queryset=None):
        return get_object_or_404(
            JournalType,
            journal_type_id=self.kwargs['journal_type_id'],
            organization_id=self.request.user.get_active_organization().id
        )

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Journal Type'
        context['back_url'] = reverse('accounting:journal_type_list')
        context['breadcrumbs'] = [
            ('Journal Types', reverse('accounting:journal_type_list')),
            ('Update Journal Type', None)
        ]
        return context

class JournalTypeDetailView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, DetailView):
    model = JournalType
    template_name = 'accounting/journal_type_detail.html'
    context_object_name = 'journal_type'
    slug_field = 'journal_type_id'
    slug_url_kwarg = 'journal_type_id'
    permission_required = ('accounting', 'journaltype', 'view')

    def get_queryset(self):
        return JournalType.objects.filter(organization=self.get_organization())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': f'Journal Type Details: {self.object.name}',
            'page_title': f'Journal Type Details: {self.object.name}',
            'breadcrumbs': [
                ('Journal Types', reverse('accounting:journal_type_list')),
                (f'Details: {self.object.name}', None)
            ]
        })
        return context


class JournalTypeCreateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, CreateView):
    model = JournalType
    form_class = JournalTypeForm
    template_name = 'accounting/journal_type_form.html'
    success_url = reverse_lazy('accounting:journal_type_list')
    permission_required = ('accounting', 'journaltype', 'add')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.organization = self.request.user.get_active_organization()
        messages.success(self.request, "Journal type created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': 'Create New Journal Type',
            'page_title': 'Create New Journal Type',
            'breadcrumbs': [
                ('Journal Types', reverse('accounting:journal_type_list')),
                ('Create New', None)
            ]
        })
        return context


class JournalTypeDeleteView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = ('accounting', 'journaltype', 'delete')
    
    def post(self, request, journal_type_id):
        journal_type = get_object_or_404(
            JournalType, 
            journal_type_id=journal_type_id,
            organization_id=request.user.get_active_organization().id
        )
        
        if journal_type.is_system_type:
            messages.error(request, "System journal types cannot be deleted.")
            return redirect('accounting:journal_type_list')
        
        # Check if there are any journals using this type
        if journal_type.journals.exists():
            messages.error(request, f"Cannot delete journal type '{journal_type.name}' because it has associated journals.")
            return redirect('accounting:journal_type_list')
        
        journal_type_name = journal_type.name
        journal_type.delete()
        messages.success(request, f"Journal type '{journal_type_name}' deleted successfully.")
        return redirect('accounting:journal_type_list')


class VoucherUDFConfigListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = VoucherUDFConfig
    template_name = 'accounting/voucher_udf_list.html'
    context_object_name = 'udf_configs'
    permission_required = ('accounting', 'voucherudfconfig', 'view')
    
    def get_queryset(self):
        return VoucherUDFConfig.objects.filter(
            voucher_mode__organization_id=self.request.user.get_active_organization().id
        ).select_related('voucher_mode')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Voucher UDF Configurations',
            'breadcrumbs': [
                ('Voucher UDF Configurations', None),
            ]
        })
        return context


class VoucherUDFConfigCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = VoucherUDFConfig
    form_class = VoucherUDFConfigForm
    template_name = 'accounting/voucher_udf_form.html'
    permission_required = ('accounting', 'voucherudfconfig', 'add')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        voucher_mode_id = self.request.GET.get('voucher_mode')
        if voucher_mode_id:
            kwargs['voucher_mode'] = get_object_or_404(
                VoucherModeConfig, 
                pk=voucher_mode_id,
                organization_id=self.request.user.get_active_organization().id
            )
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "UDF configuration created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_udf_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': 'Create New UDF Configuration',
            'page_title': 'Create New UDF Configuration',
            'breadcrumbs': [
                ('Voucher UDF Configurations', reverse('accounting:voucher_udf_list')),
                ('Create New', None)
            ]
        })
        return context


class VoucherUDFConfigUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = VoucherUDFConfig
    form_class = VoucherUDFConfigForm
    template_name = 'accounting/voucher_udf_form.html'
    permission_required = ('accounting', 'voucherudfconfig', 'change')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        kwargs['voucher_mode'] = self.object.voucher_mode
        return kwargs
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "UDF configuration updated successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_udf_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': f'Update UDF Configuration: {self.object.display_name}',
            'page_title': f'Update UDF Configuration: {self.object.display_name}',
            'breadcrumbs': [
                ('Voucher UDF Configurations', reverse('accounting:voucher_udf_list')),
                (f'Update {self.object.display_name}', None)
            ]
        })
        return context

class VoucherUDFConfigDeleteView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = ('accounting', 'voucherudfconfig', 'delete')
    
    def post(self, request, pk):
        udf_config = get_object_or_404(
            VoucherUDFConfig, 
            pk=pk, 
            voucher_mode__organization_id=request.user.get_active_organization().id
        )
        udf_name = udf_config.display_name
        udf_config.delete()
        messages.success(request, f"UDF configuration '{udf_name}' deleted successfully.")
        return redirect('accounting:voucher_udf_list')

def get_next_account_code(request):
    org_id = request.GET.get("organization")
    parent_id = request.GET.get("parent_account")
    account_type = request.GET.get("account_type")
    if not org_id or org_id == "undefined":
        return JsonResponse({"error": "Missing or invalid organization"}, status=400)
    if not parent_id and not account_type:
        return JsonResponse({"next_code": ""})  # Don't try to look up if both are empty
    if account_type == "":
        account_type = None
    if parent_id == "":
        parent_id = None
    try:
        next_code = ChartOfAccount.get_next_code(org_id, parent_id, account_type)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"next_code": next_code})

# def get_next_account_code(self, root_prefix, org_id):
#     """
#     Get the next account code based on the root prefix and organization ID.
#     """
#     top_levels = ChartOfAccount.objects.filter(
#         parent_account__isnull=True,
#         organization_id=org_id,
#         account_code__startswith=root_prefix  # Use full root_prefix
#     )
#     max_code = 0
#     for acc in top_levels:
#         try:
#             acc_num = int(acc.account_code)
#             if str(acc_num).startswith(root_prefix) and acc_num > max_code:  # Use full root_prefix
#                 max_code = acc_num
#         except ValueError:
#             continue
#     return max_code


# This part seems to be a part of a view function
def get_next_account_code_view(self, request):
    try:
        root_prefix = self.request.GET.get('root_prefix')
        org_id = self.request.GET.get('org_id')
        step = self.request.GET.get('step')  # Assuming step is passed as a GET parameter

        if not all([root_prefix, org_id, step]):
            return JsonResponse({'error': 'root_prefix, org_id, and step are required'}, status=400)

        max_code = self.get_next_account_code(root_prefix, org_id)

        if max_code >= int(root_prefix):
            next_code = str(max_code + int(step)).zfill(len(root_prefix))
        else:
            next_code = root_prefix

        return JsonResponse({'next_code': next_code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
# def get_next_account_code(request):
#     """
#     AJAX endpoint to get the next account code based on account_type and/or parent_account.
#     """
#     org_id = request.GET.get('organization')
#     account_type_id = request.GET.get('account_type')
#     parent_id = request.GET.get('parent_account')

#     if not org_id:
#         return JsonResponse({'error': 'Organization required'}, status=400)

#     try:
#         if parent_id:
#             parent = ChartOfAccount.objects.get(pk=parent_id, organization_id=org_id)
#             # Generate next child code
#             siblings = ChartOfAccount.objects.filter(parent_account=parent, organization_id=org_id)
#             sibling_codes = siblings.values_list('account_code', flat=True)
#             base_code = parent.account_code
#             max_suffix = 0
#             for code in sibling_codes:
#                 if code.startswith(base_code + "."):
#                     try:
#                         suffix = int(code.replace(base_code + ".", ""))
#                         if suffix > max_suffix:
#                             max_suffix = suffix
#                     except ValueError:
#                         continue
#             next_suffix = max_suffix + 1
#             next_code = f"{base_code}.{next_suffix:02d}"
#         elif account_type_id:
#             account_type = AccountType.objects.get(pk=account_type_id)
#             root_prefix = account_type.root_code_prefix or ChartOfAccount.NATURE_ROOT_CODE.get(account_type.nature, '9000')
#             step = account_type.root_code_step or ChartOfAccount.ROOT_STEP
#             top_levels = ChartOfAccount.objects.filter(
#                 parent_account__isnull=True,
#                 organization_id=org_id,
#                 account_code__startswith=root_prefix[0]
#             )
#             max_code = 0
#             for acc in top_levels:
#                 try:
#                     acc_num = int(acc.account_code)
#                     if str(acc_num).startswith(root_prefix[0]) and acc_num > max_code:
#                         max_code = acc_num
#                 except ValueError:
#                     continue
#             if max_code >= int(root_prefix):
#                 next_code = str(max_code + step).zfill(len(root_prefix))
#             else:
#                 next_code = root_prefix
#         else:
#             return JsonResponse({'error': 'account_type or parent_account required'}, status=400)
#         return JsonResponse({'next_code': next_code})
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)

class ChartOfAccountFormFieldsView(LoginRequiredMixin, View):
    """HTMX view for dynamic form fields."""
    template_name = "accounting/chart_of_accounts_form_fields.html"

    @method_decorator(require_htmx)
    def get(self, request, *args, **kwargs):
        form = ChartOfAccountForm(organization=request.user.organization)
        return render(request, self.template_name, {'form': form})
# class ChartOfAccountCreateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, CreateView):

#     model = ChartOfAccount
#     form_class = ChartOfAccountForm
#     template_name = 'accounting/chart_of_accounts_form.html'
#     success_url = reverse_lazy('accounting:chart_of_accounts_list')
#     permission_required = ('accounting', 'chartofaccount', 'add')

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['organization'] = self.request.user.organization
#         return kwargs

#     def form_valid(self, form):
#         form.instance.organization = self.get_organization()
#         return super().form_valid(form)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['form_title'] = 'Create Chart of Account'
#         context['back_url'] = reverse('accounting:chart_of_accounts_list')
#         context['breadcrumbs'] = [
#             ('Chart of Accounts', reverse('accounting:chart_of_accounts_list')),
#             ('Create Chart of Account', None)
#         ]
#         return context

@login_required
@csrf_exempt
def chart_of_accounts_create(request):
    initial = get_pending_form_initial(request)
    clear_storage_script = None
    org = getattr(request.user, 'organization', None)
    if request.method == 'POST':
        form = ChartOfAccountForm(request.POST, organization=org)
        # Ensure organization is set on the instance before validation
        if org is not None:
            form.instance.organization = org
        if form.is_valid():
            form.save()
            clear_pending_form(request)
            clear_storage_script = """
            <script>
            document.body.dispatchEvent(new Event('clearFormStorage'));
            </script>
            """
            # HTMX-aware redirect
            if request.headers.get('HX-Request'):
                from django.http import HttpResponse
                response = HttpResponse()
                response['HX-Redirect'] = reverse('accounting:chart_of_accounts_list')
                response['HX-Trigger'] = 'clearFormStorage'
                return response
            else:
                response = redirect('accounting:chart_of_accounts_list')
                response['HX-Trigger'] = 'clearFormStorage'
                return response
    else:
        form = ChartOfAccountForm(initial=initial, organization=org)
    context = {'form': form, 'form_post_url': request.path}
    if clear_storage_script:
        context['clear_storage_script'] = clear_storage_script
    return render(request, 'accounting/chart_of_accounts_form.html', context)

# Financial Reports Views
class TrialBalanceView(LoginRequiredMixin, UserOrganizationMixin, TemplateView):
    template_name = 'accounting/reports/trial_balance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        if not organization:
            context['error'] = 'No active organization found.'
            return context
        
        # Get period from request or use current period
        period_id = self.request.GET.get('period')
        if period_id:
            period = AccountingPeriod.objects.filter(
                id=period_id,
                fiscal_year__organization_id=organization.id
            ).first()
        else:
            period = AccountingPeriod.objects.filter(
                fiscal_year__organization_id=organization.id,
                is_current=True
            ).first()
        
        if not period:
            context['error'] = 'No accounting period found.'
            return context
        
        # Get trial balance data
        trial_balance = self.get_trial_balance(organization, period)
        
        context.update({
            'organization': organization,
            'period': period,
            'trial_balance': trial_balance,
            'page_title': 'Trial Balance',
            'breadcrumbs': [
                ('Reports', None),
                ('Trial Balance', None),
            ]
        })
        
        return context
    
    def get_trial_balance(self, organization, period):
        """Get trial balance for the period"""
        # Get all accounts with their balances
        accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            is_active=True
        ).order_by('account_code')
        
        trial_balance = []
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        for account in accounts:
            # Get account balance from GeneralLedger
            ledger_entries = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            )
            
            total_debit = ledger_entries.aggregate(
                total=Sum('debit_amount')
            )['total'] or Decimal('0')
            
            total_credit = ledger_entries.aggregate(
                total=Sum('credit_amount')
            )['total'] or Decimal('0')
            
            # Calculate net balance based on account type
            if account.account_type.nature in ['asset', 'expense']:
                net_balance = total_debit - total_credit
                normal_balance = 'Debit'
            else:
                net_balance = total_credit - total_debit
                normal_balance = 'Credit'
            
            trial_balance.append({
                'account_code': account.account_code,
                'account_name': account.account_name,
                'account_type': account.account_type.name,
                'debit_amount': total_debit,
                'credit_amount': total_credit,
                'net_balance': net_balance,
                'normal_balance': normal_balance,
            })
            
            total_debits += total_debit
            total_credits += total_credit
        
        return {
            'accounts': trial_balance,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'difference': total_debits - total_credits,
        }


class IncomeStatementView(LoginRequiredMixin, UserOrganizationMixin, TemplateView):
    template_name = 'accounting/reports/income_statement.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        if not organization:
            context['error'] = 'No active organization found.'
            return context
        
        # Get period from request or use current period
        period_id = self.request.GET.get('period')
        if period_id:
            period = AccountingPeriod.objects.filter(
                id=period_id,
                fiscal_year__organization_id=organization.id
            ).first()
        else:
            period = AccountingPeriod.objects.filter(
                fiscal_year__organization_id=organization.id,
                is_current=True
            ).first()
        
        if not period:
            context['error'] = 'No accounting period found.'
            return context
        
        # Get income statement data
        income_statement = self.get_income_statement(organization, period)
        
        context.update({
            'organization': organization,
            'period': period,
            'income_statement': income_statement,
            'page_title': 'Income Statement',
            'breadcrumbs': [
                ('Reports', None),
                ('Income Statement', None),
            ]
        })
        
        return context
    
    def get_income_statement(self, organization, period):
        """Get income statement for the period"""
        # Get revenue accounts
        revenue_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='income',
            is_active=True
        )
        
        # Get expense accounts
        expense_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='expense',
            is_active=True
        )
        
        # Calculate revenue
        total_revenue = Decimal('0')
        revenue_details = []
        for account in revenue_accounts:
            credit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            
            revenue_details.append({
                'account_name': account.account_name,
                'amount': credit_amount,
            })
            total_revenue += credit_amount
        
        # Calculate expenses
        total_expenses = Decimal('0')
        expense_details = []
        for account in expense_accounts:
            debit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            
            expense_details.append({
                'account_name': account.account_name,
                'amount': debit_amount,
            })
            total_expenses += debit_amount
        
        # Calculate net income
        net_income = total_revenue - total_expenses
        
        return {
            'revenue_details': revenue_details,
            'total_revenue': total_revenue,
            'expense_details': expense_details,
            'total_expenses': total_expenses,
            'net_income': net_income,
        }


class BalanceSheetView(LoginRequiredMixin, UserOrganizationMixin, TemplateView):
    template_name = 'accounting/reports/balance_sheet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        if not organization:
            context['error'] = 'No active organization found.'
            return context
        
        # Get period from request or use current period
        period_id = self.request.GET.get('period')
        if period_id:
            period = AccountingPeriod.objects.filter(
                id=period_id,
                fiscal_year__organization_id=organization.id
            ).first()
        else:
            period = AccountingPeriod.objects.filter(
                fiscal_year__organization_id=organization.id,
                is_current=True
            ).first()
        
        if not period:
            context['error'] = 'No accounting period found.'
            return context
        
        # Get balance sheet data
        balance_sheet = self.get_balance_sheet(organization, period)
        
        context.update({
            'organization': organization,
            'period': period,
            'balance_sheet': balance_sheet,
            'page_title': 'Balance Sheet',
            'breadcrumbs': [
                ('Reports', None),
                ('Balance Sheet', None),
            ]
        })
        
        return context
    
    def get_balance_sheet(self, organization, period):
        """Get balance sheet for the period"""
        # Get asset accounts
        asset_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='asset',
            is_active=True
        )
        
        # Get liability accounts
        liability_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='liability',
            is_active=True
        )
        
        # Get equity accounts
        equity_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='equity',
            is_active=True
        )
        
        # Calculate assets
        total_assets = Decimal('0')
        asset_details = []
        for account in asset_accounts:
            debit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            
            credit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            
            balance = debit_amount - credit_amount
            
            asset_details.append({
                'account_name': account.account_name,
                'balance': balance,
            })
            total_assets += balance
        
        # Calculate liabilities
        total_liabilities = Decimal('0')
        liability_details = []
        for account in liability_accounts:
            debit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            
            credit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            
            balance = credit_amount - debit_amount
            
            liability_details.append({
                'account_name': account.account_name,
                'balance': balance,
            })
            total_liabilities += balance
        
        # Calculate equity
        total_equity = Decimal('0')
        equity_details = []
        for account in equity_accounts:
            debit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            
            credit_amount = GeneralLedger.objects.filter(
                organization_id=organization.id,
                period=period,
                account=account
            ).aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            
            balance = credit_amount - debit_amount
            
            equity_details.append({
                'account_name': account.account_name,
                'balance': balance,
            })
            total_equity += balance
        
        return {
            'asset_details': asset_details,
            'total_assets': total_assets,
            'liability_details': liability_details,
            'total_liabilities': total_liabilities,
            'equity_details': equity_details,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities + total_equity,
        }


class ReportsListView(LoginRequiredMixin, UserOrganizationMixin, TemplateView):
    template_name = 'accounting/reports/reports_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        
        if not organization:
            context['error'] = 'No active organization found.'
            return context
        
        # Get available periods
        periods = AccountingPeriod.objects.filter(
            fiscal_year__organization_id=organization.id
        ).order_by('-start_date')
        
        context.update({
            'organization': organization,
            'periods': periods,
            'page_title': 'Financial Reports',
            'breadcrumbs': [
                ('Reports', None),
            ]
        })
        
        return context