from django.forms import ValidationError
from .models import *
from .forms import *
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .views_mixins import UserOrganizationMixin, PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.contrib import messages  # Add this import for messages
from django.db import transaction    # Add this import for transaction
from django.http import HttpResponseServerError, HttpResponse  # Add this import for error handling and HttpResponse
from django.shortcuts import get_object_or_404, redirect  # Add this import for get_object_or_404
import logging

logger = logging.getLogger(__name__)

class FiscalYearCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = FiscalYear
    form_class = FiscalYearForm
    template_name = 'accounting/fiscal_year_form.html'
    success_url = reverse_lazy('accounting:fiscal_year_list')
    permission_required = ('accounting', 'fiscalyear', 'add')

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")

    def get_initial(self):
        initial = super().get_initial()
        from .models import AutoIncrementCodeGenerator
        code_generator = AutoIncrementCodeGenerator(FiscalYear, 'code', prefix='FY', suffix='')
        initial['code'] = code_generator.generate_code()
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Fiscal year created successfully.")
        form.instance.organization = self.request.user.get_active_organization()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Fiscal Year'
        context['back_url'] = reverse('accounting:fiscal_year_list')
        return context

class CostCenterCreateView(LoginRequiredMixin, UserOrganizationMixin, CreateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'accounting/costcenter_form.html'
    success_url = reverse_lazy('accounting:costcenter_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization 
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Cost Center'
        context['back_url'] = reverse('accounting:costcenter_list')
        context['breadcrumbs'] = [
            ('Cost Centers', reverse('accounting:costcenter_list')),
            ('Create Cost Center', None)
        ]
        return context

class TaxTypeCreateView(LoginRequiredMixin, CreateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = 'accounting/tax_type_form.html'
    success_url = reverse_lazy('accounting:tax_type_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Tax Type'
        context['back_url'] = reverse('accounting:tax_type_list')
        context['breadcrumbs'] = [
            ('Tax Types', reverse('accounting:tax_type_list')),
            ('Create Tax Type', None)
        ]
        return context
 
class TaxAuthorityCreateView(LoginRequiredMixin, CreateView):
    model = TaxAuthority
    form_class = TaxAuthorityForm
    template_name = 'accounting/tax_authority_form.html'
    success_url = reverse_lazy('accounting:tax_authority_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Tax Authority'
        context['back_url'] = reverse('accounting:tax_authority_list')
        context['breadcrumbs'] = [
            ('Tax Authorities', reverse('accounting:tax_authority_list')),
            ('Create Tax Authority', None)
        ]
        return context


class AccountTypeCreateView(LoginRequiredMixin, CreateView):
    model = AccountType
    form_class = AccountTypeForm
    template_name = 'accounting/account_type_form.html'
    success_url = reverse_lazy('accounting:account_type_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Account Type'
        context['back_url'] = reverse('accounting:account_type_list')
        context['breadcrumbs'] = [
            ('Account Types', reverse('accounting:account_type_list')),
            ('Create Account Type', None)
        ]
        return context


class ChartOfAccountCreateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, CreateView):
    model = ChartOfAccount
    form_class = ChartOfAccountForm
    template_name = 'accounting/chart_of_accounts_form.html'
    success_url = reverse_lazy('accounting:chart_of_accounts_list')
    permission_required = ('accounting', 'chartofaccount', 'add')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_organization()
        return kwargs

    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.instance.organization = self.get_organization()
                form.instance.created_by = self.request.user
                
                # Save the form
                response = super().form_valid(form)
                
                # If it's an HTMX request, return a success message
                if self.request.headers.get('HX-Request'):
                    messages.success(self.request, "Chart of Account created successfully.")
                    return HttpResponse(
                        f'<div class="alert alert-success">Chart of Account created successfully. Redirecting...</div>'
                        f'<script>setTimeout(function() {{ window.location.href = "{self.success_url}"; }}, 1000);</script>',
                        status=200
                    )
                
                messages.success(self.request, "Chart of Account created successfully.")
                return response
                
        except Exception as e:
            logger.error(f"Error creating chart of account: {str(e)}")
            if self.request.headers.get('HX-Request'):
                return HttpResponse(
                    f'<div class="alert alert-danger">Error creating Chart of Account: {str(e)}</div>',
                    status=400
                )
            messages.error(self.request, f"Error creating Chart of Account: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.error(f"Form validation errors: {form.errors}")
        if self.request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return HttpResponse(html, status=400)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': 'Create Chart of Account',
            'page_title': 'Create Chart of Account',
            'breadcrumbs': [
                ('Chart of Accounts', reverse('accounting:chart_of_accounts_list')),
                ('Create Chart of Account', None)
            ],
            'form_post_url': reverse('accounting:chart_of_accounts_create')
        })
        return context

class CurrencyCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'accounting/currency_form.html'
    success_url = reverse_lazy('accounting:currency_list')
    permission_required = ('accounting', 'currency', 'add')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Currency'
        context['back_url'] = reverse('accounting:currency_list')
        context['breadcrumbs'] = [
            ('Currencies', reverse('accounting:currency_list')),
            ('Create Currency', None)
        ]
        return context

class CurrencyExchangeRateCreateView(LoginRequiredMixin, CreateView):
    model = CurrencyExchangeRate
    form_class = CurrencyExchangeRateForm
    template_name = 'accounting/currency_exchange_rate_form.html'
    success_url = reverse_lazy('accounting:exchange_rate_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        messages.success(self.request, "Currency exchange rate created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Exchange Rate'
        context['back_url'] = reverse('accounting:exchange_rate_list')
        context['breadcrumbs'] = [
            ('Exchange Rates', reverse('accounting:exchange_rate_list')),
            ('Create Exchange Rate', None)
        ]
        return context

class VoucherModeConfigCreateView(LoginRequiredMixin, CreateView):
    model = VoucherModeConfig
    form_class = VoucherModeConfigForm
    template_name = 'accounting/voucher_config_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.get_active_organization()
        form.instance.created_by = self.request.user
        messages.success(self.request, "Voucher configuration created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': 'Create Voucher Configuration',
            'page_title': 'Create Voucher Configuration',
            'breadcrumbs': [
                ('Voucher Configurations', reverse('accounting:voucher_config_list')),
                ('Create Voucher Configuration', None)
            ]
        })
        return context


class VoucherModeDefaultCreateView(LoginRequiredMixin, CreateView):
    model = VoucherModeDefault
    form_class = VoucherModeDefaultForm
    template_name = 'accounting/voucher_default_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        kwargs['config_id'] = self.kwargs['config_id']
        return kwargs
    
    def form_valid(self, form):
        config = get_object_or_404(VoucherModeConfig, pk=self.kwargs['config_id'], organization=self.request.user.get_active_organization())
        form.instance.config = config
        messages.success(self.request, "Voucher default line created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': self.kwargs['config_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = get_object_or_404(VoucherModeConfig, pk=self.kwargs['config_id'], organization=self.request.user.get_active_organization())
        context.update({
            'form_title': f'Add Default Line to {config.name}',
            'page_title': f'Add Default Line: {config.name}',
            'breadcrumbs': [
                ('Voucher Configurations', reverse('accounting:voucher_config_list')),
                (f'{config.name} Details', reverse('accounting:voucher_config_detail', kwargs={'pk': config.pk})),
                ('Add Default Line', None)
            ]
        })
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'accounting/project_form.html'
    success_url = reverse_lazy('accounting:project_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Project'
        context['back_url'] = reverse('accounting:project_list')
        context['breadcrumbs'] = [
            ('Projects', reverse('accounting:project_list')),
            ('Create Project', None)
        ]
        return context

class AccountingPeriodCreateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, CreateView):
    model = AccountingPeriod
    form_class = AccountingPeriodForm
    template_name = 'accounting/accounting_period_form.html'
    success_url = reverse_lazy('accounting:accounting_period_list')
    permission_required = ('accounting', 'accountingperiod', 'add')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Accounting Period'
        context['back_url'] = reverse('accounting:accounting_period_list')
        return context

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'accounting/department_form.html'
    success_url = reverse_lazy('accounting:department_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Department'
        context['back_url'] = reverse('accounting:department_list')
        context['breadcrumbs'] = [
            ('Departments', reverse('accounting:department_list')),
            ('Create Department', None)
        ]
        return context


class JournalCreateView(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = 'accounting/journal_form.html'
    success_url = reverse_lazy('accounting:journal_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = JournalLineFormSet(self.request.POST, instance=self.object)
        else:
            context['lines'] = JournalLineFormSet(instance=self.object)
        
        context.update({
            'form_title': 'Create Journal',
            'page_title': 'Create Journal',
            'breadcrumbs': [
                ('Journals', reverse('accounting:journal_list')),
                ('Create Journal', None)
            ]
        })
        return context
    
   
    def form_valid(self, form):
        try:
            context = self.get_context_data()
            lines = context['lines']
            
            with transaction.atomic():
                form.instance.organization = self.request.user.get_active_organization()
                form.instance.created_by = self.request.user
                self.object = form.save()
                
                if lines.is_valid():
                    lines.instance = self.object
                    lines.save()
                    for lf in lines.forms:
                        if lf.cleaned_data.get("DELETE"):
                            continue
                        if lf.cleaned_data.get("save_as_default"):
                            jt = form.cleaned_data.get("journal_type")
                            org = self.request.user.get_active_organization()
                            config = VoucherModeConfig.objects.filter(
                                organization=org,
                                journal_type=jt,
                                is_default=True,
                            ).first()
                            if config:
                                order = config.defaults.count() + 1
                                VoucherModeDefault.objects.create(
                                    config=config,
                                    account=lf.cleaned_data.get("account"),
                                    default_debit=lf.cleaned_data.get("debit_amount", 0) > 0,
                                    default_credit=lf.cleaned_data.get("credit_amount", 0) > 0,
                                    default_amount=lf.cleaned_data.get("debit_amount") or lf.cleaned_data.get("credit_amount"),
                                    default_tax_code=lf.cleaned_data.get("tax_code"),
                                    default_department=lf.cleaned_data.get("department").pk if lf.cleaned_data.get("department") else 0,
                                    default_project=lf.cleaned_data.get("project").pk if lf.cleaned_data.get("project") else 0,
                                    default_cost_center=lf.cleaned_data.get("cost_center").pk if lf.cleaned_data.get("cost_center") else 0,
                                    default_description=lf.cleaned_data.get("description"),
                                    display_order=order,
                                    created_by=self.request.user,
                                )
                else:
                    # If line forms are invalid, return form_invalid
                    messages.error(self.request, "Please correct the errors in the journal lines.")
                    return self.form_invalid(form)  # Re-render with errors

            messages.success(self.request, "Journal created successfully.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating journal: {e}")
            messages.error(self.request, f"An error occurred while creating the journal: {e}")
            return HttpResponseServerError("Internal Server Error") # More informative error
        
        
class JournalTypeCreateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, CreateView):
    model = JournalType
    form_class = JournalTypeForm
    template_name = 'accounting/journal_type_form.html'
    success_url = reverse_lazy('accounting:journal_type_list')
    permission_required = ('accounting', 'journaltype', 'add')

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Journal Type'
        context['back_url'] = reverse('accounting:journal_type_list')
        return context
