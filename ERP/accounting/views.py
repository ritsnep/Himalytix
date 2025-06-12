from asyncio.log import logger
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import AccountType, Currency, CurrencyExchangeRate, FiscalYear, TaxAuthority, TaxType
from .forms import AccountTypeForm, ChartOfAccountForm, CostCenterForm, CurrencyExchangeRateForm, CurrencyForm, DepartmentForm, FiscalYearForm, ProjectForm, TaxAuthorityForm, TaxTypeForm
from django.contrib import messages
from django.db.models import F


from .models import (
    FiscalYear, GeneralLedger, Journal, JournalLine, JournalType, ChartOfAccount, 
    AccountingPeriod, TaxCode, Department, Project, CostCenter,
    VoucherModeConfig, VoucherModeDefault
)
from .forms import (
    JournalForm, JournalLineForm, JournalLineFormSet,
    VoucherModeConfigForm, VoucherModeDefaultForm
)


from django.urls import reverse_lazy
from utils.htmx import require_htmx
from usermanagement.utils import require_permission
from usermanagement.utils import PermissionUtils
from django.forms import inlineformset_factory

class UserOrganizationMixin:
    """
    Mixin to provide self.organization = request.user.organization
    and inject it into form kwargs and queryset.
    """
    def get_organization(self):
        # Use the user's active organization if available
        user = getattr(self.request, "user", None)
        if user and hasattr(user, "get_active_organization"):
            org = user.get_active_organization()
            if org:
                return org
        # Fallback to user.organization if present
        return getattr(user, "organization", None)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        org = self.get_organization()
        if org:
            kwargs['organization'] = org
        return kwargs

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.get_organization()
        # Only filter if the model has an organization field
        if org and hasattr(qs.model, "organization_id"):
            return qs.filter(organization=org)
        return qs

class PermissionRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'permission_required'):
            return super().dispatch(request, *args, **kwargs)
        
        module, entity, action = self.permission_required
        if not PermissionUtils.has_permission(request.user, request.user.organization, module, entity, action):
            return HttpResponseForbidden()
        
        return super().dispatch(request, *args, **kwargs)

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
        form.instance.organization = self.get_organization()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Fiscal Year'
        context['back_url'] = reverse('accounting:fiscal_year_list')
        return context

class FiscalYearUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, UpdateView):
    model = FiscalYear
    form_class = FiscalYearForm
    template_name = 'accounting/fiscal_year_form.html'
    success_url = reverse_lazy('accounting:fiscal_year_list')
    permission_required = ('accounting', 'fiscalyear', 'change')
    
    slug_field = 'fiscal_year_id'
    slug_url_kwarg = 'fiscal_year_id'

    def get_queryset(self):
        return super().get_queryset()

    def get_object(self, queryset=None):
        return get_object_or_404(
            FiscalYear,
            fiscal_year_id=self.kwargs['fiscal_year_id'],
            organization=self.request.user.get_active_organization()
        )

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        messages.success(self.request, "Fiscal year updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form_title': 'Update Fiscal Year',
            'page_title': 'Update Fiscal Year',
            'breadcrumbs': [
                ('Fiscal Years', reverse('accounting:fiscal_year_list')),
                ('Update', None)
            ]
        })
        return context

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
        return CostCenter.objects.filter(organization_id=self.request.user.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse('accounting:costcenter_create')
        context['create_button_text'] = 'New Cost Center'
        context['page_title'] = 'Cost Centers'
        context['breadcrumbs'] = [
            ('Cost Centers', None),
        ]
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

class CostCenterUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UserOrganizationMixin, UpdateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'accounting/costcenter_form.html'
    success_url = reverse_lazy('accounting:costcenter_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def get_queryset(self):
        return CostCenter.objects.filter(organization=self.request.user.organization)
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Cost Center'
        context['back_url'] = reverse('accounting:costcenter_list')
        context['breadcrumbs'] = [
            ('Cost Centers', reverse('accounting:costcenter_list')),
            ('Update Cost Center', None)
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
                else:
                    # If line forms are invalid, return form_invalid
                    messages.error(self.request, "Please correct the errors in the journal lines.")
                    return self.form_invalid(form) # Re-render with errors

            messages.success(self.request, "Journal created successfully.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating journal: {e}")
            messages.error(self.request, f"An error occurred while creating the journal: {e}")
            return HttpResponseServerError("Internal Server Error") # More informative error

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
            # Create GL entries
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
                
                # Update account balances
                line.account.current_balance += (line.debit_amount - line.credit_amount)
                line.account.save()
            
            journal.status = 'posted'
            journal.posted_at = timezone.now()
            journal.posted_by = request.user
            journal.save()
        
        return JsonResponse({'success': True})


class JournalUpdateView(LoginRequiredMixin, UpdateView):
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
            'form_title': f'Update Journal: {self.object.journal_number}',
            'page_title': f'Update Journal: {self.object.journal_number}',
            'breadcrumbs': [
                ('Journals', reverse('accounting:journal_list')),
                (f'Update Journal: {self.object.journal_number}', None)
            ]
        })
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        
        with transaction.atomic():
            form.instance.updated_by = self.request.user
            self.object = form.save()
            
            if lines.is_valid():
                lines.instance = self.object
                lines.save()
            else:
                # If line forms are invalid, return form_invalid
                messages.error(self.request, "Please correct the errors in the journal lines.")
                return self.form_invalid(form) # Re-render with errors
        messages.success(self.request, "Journal updated successfully.") # Add success message
        return super().form_valid(form)

class HTMXAccountAutocompleteView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('query', '')
        accounts = ChartOfAccount.objects.filter(
            organization=request.user.organization,
            account_code__icontains=query
        )[:10]
        results = [{'id': a.account_id, 'text': f"{a.account_code} - {a.account_name}"} for a in accounts]
        return JsonResponse({'results': results})

class HTMXJournalLineFormView(LoginRequiredMixin, View):
    def get(self, request):
        organization = request.user.get_active_organization()
        form_index = request.GET.get('index', '0') # Get the index for the new form

        # Create a single empty form from the formset
        # We need a dummy instance to create the formset for a single extra form
        # Or, we can just instantiate JournalLineForm directly with a prefix
        form = JournalLineForm(prefix=f'lines-{form_index}', organization=organization)
        
        # Manually set required attributes for new form for client-side validation
        # These are set in the forms.py now, but can be reinforced here if needed
        # form.fields['account'].widget.attrs['required'] = 'required'
        # form.fields['debit_amount'].widget.attrs['required'] = 'required'
        # form.fields['credit_amount'].widget.attrs['required'] = 'required'

        return render(request, 'accounting/partials/journal_line_form.html', {'form': form})

# Voucher Mode Views
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


class VoucherModeConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = VoucherModeConfig
    form_class = VoucherModeConfigForm
    template_name = 'accounting/voucher_config_form.html'
    
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

class VoucherModeConfigDetailView(LoginRequiredMixin, DetailView):
    model = VoucherModeConfig
    template_name = 'accounting/voucher_config_detail.html'
    context_object_name = 'config'

    def get_queryset(self):
        return VoucherModeConfig.objects.filter(organization=self.request.user.get_active_organization())

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


class VoucherModeDefaultUpdateView(LoginRequiredMixin, UpdateView):
    model = VoucherModeDefault
    form_class = VoucherModeDefaultForm
    template_name = 'accounting/voucher_default_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.get_active_organization()
        kwargs['config_id'] = self.object.config_id
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': self.object.config_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = get_object_or_404(VoucherModeConfig, pk=self.object.config_id, organization=self.request.user.get_active_organization())
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

class VoucherModeDefaultDeleteView(LoginRequiredMixin, View):
    @method_decorator(require_permission('accounting','vouchermodedefault','delete'))
    def post(self, request, pk):
        default = get_object_or_404(VoucherModeDefault, pk=pk, config__organization=request.user.get_active_organization())
        config_id = default.config_id
        default.delete()
        messages.success(request, "Voucher default line deleted successfully.")
        return redirect(reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': config_id}))

class VoucherEntryView(LoginRequiredMixin, View):

    template_name = 'accounting/voucher_entry.html'
    
    def get(self, request, config_id=None):
        organization = request.user.get_active_organization()
        if config_id:
            config = get_object_or_404(VoucherModeConfig, pk=config_id, organization=organization)
        else:
            config = VoucherModeConfig.objects.filter(
                organization=organization,
                is_default=True
            ).first()
        
        if not config:
            messages.warning(request, "No default voucher configuration found. Please create one.")
            return redirect('accounting:voucher_config_list')
        
        journal_form = JournalForm(organization=organization, initial={
            'journal_type': config.journal_type,
            'currency_code': config.default_currency,
        })
        
        # Populate initial lines from defaults
        initial_lines = []
        for default in config.defaults.all().order_by('display_order'):
            initial_lines.append({
                'account': default.account,
                'description': default.default_description,
                'debit_amount': default.default_amount if default.default_debit else 0,
                'credit_amount': default.default_amount if default.default_credit else 0,
                'department': default.default_department,
                'project': default.default_project,
                'cost_center': default.default_cost_center,
                'tax_code': default.default_tax_code,
                'memo': default.default_description,
            })
        
        JournalLineFormSet = inlineformset_factory(
            Journal, JournalLine,
            form=JournalLineForm,
            extra=max(len(initial_lines), 1),
            can_delete=True,
            fields=[
                'account', 'description', 'debit_amount', 
                'credit_amount', 'department', 'project',
                'cost_center', 'tax_code', 'memo'
            ]
        )
        lines_formset = JournalLineFormSet(initial=initial_lines, form_kwargs={'organization': organization})


        context = {
            'config': config,
            'journal_form': journal_form,
            'lines': lines_formset,
            'form_title': f'Voucher Entry: {config.name}',
            'page_title': f'Voucher Entry: {config.name}',
            'breadcrumbs': [
                ('Voucher Entry', reverse('accounting:voucher_entry')),
                (config.name, None)
            ]
        }
        
        return render(request, self.template_name, context)

    def post(self, request, config_id=None):
        organization = request.user.get_active_organization()
        if config_id:
            config = get_object_or_404(VoucherModeConfig, pk=config_id, organization=organization)
        else:
            config = VoucherModeConfig.objects.filter(
                organization=organization,
                is_default=True
            ).first()

        if not config:
            messages.error(request, "No default voucher configuration found. Cannot create voucher.")
            return redirect('accounting:voucher_config_list')

        journal_form = JournalForm(request.POST, organization=organization)

        JournalLineFormSet = inlineformset_factory(
            Journal, JournalLine,
            form=JournalLineForm,
            extra=0,
            can_delete=True,
            fields=[
                'account', 'description', 'debit_amount', 
                'credit_amount', 'department', 'project',
                'cost_center', 'tax_code', 'memo'
            ]
        )
        lines_formset = JournalLineFormSet(request.POST, form_kwargs={'organization': organization})

        if journal_form.is_valid() and lines_formset.is_valid():
            try:
                with transaction.atomic():
                    journal = journal_form.save(commit=False)
                    journal.organization = organization
                    journal.created_by = request.user
                    journal.save()

                    lines = lines_formset.save(commit=False)
                    for line in lines:
                        line.journal = journal
                        line.save()
                    
                    # Handle deletions in formset
                    for deleted_form in lines_formset.deleted_forms:
                        deleted_form.instance.delete()

                messages.success(request, "Voucher entry created successfully.")
                return redirect('accounting:journal_detail', pk=journal.pk)

            except Exception as e:
                messages.error(request, f"Error saving voucher entry: {e}")
                logger.error(f"Error saving voucher entry: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")

        context = {
            'config': config,
            'journal_form': journal_form,
            'lines': lines_formset,
            'form_title': f'Voucher Entry: {config.name}',
            'page_title': f'Voucher Entry: {config.name}',
            'breadcrumbs': [
                ('Voucher Entry', reverse('accounting:voucher_entry')),
                (config.name, None)
            ]
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
    
class ChartOfAccountListPartial(ChartOfAccountListView):
    """HTMX partial for chart of accounts list."""
    template_name = "accounting/chart_of_accounts_list_partial.html"

    @method_decorator(require_htmx)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


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
        form.instance.organization = self.get_organization()
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Chart of Account'
        context['back_url'] = reverse('accounting:chart_of_accounts_list')
        context['breadcrumbs'] = [
            ('Chart of Accounts', reverse('accounting:chart_of_accounts_list')),
            ('Create Chart of Account', None)
        ]
        return context

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
        return ChartOfAccount.objects.filter(organization=self.request.user.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Update Chart of Account'
        context['back_url'] = reverse('accounting:chart_of_accounts_list')
        context['breadcrumbs'] = [
            ('Chart of Accounts', reverse('accounting:chart_of_accounts_list')),
            ('Update Chart of Account', None)
        ]
        return context

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
        return TaxAuthority.objects.filter(organization=self.request.user.organization)

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
        return TaxType.objects.filter(organization=self.request.user.organization)

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
            organization=self.request.user.organization
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
        return Project.objects.filter(organization=self.request.user.organization)

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
