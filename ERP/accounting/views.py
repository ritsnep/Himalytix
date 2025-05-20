# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone
from .models import (
    GeneralLedger, Journal, JournalLine, JournalType, ChartOfAccount, 
    AccountingPeriod, TaxCode, Department, Project, CostCenter,
    VoucherModeConfig, VoucherModeDefault
)
from .forms import (
    JournalForm, JournalLineForm, JournalLineFormSet,
    VoucherModeConfigForm, VoucherModeDefaultForm
)

class JournalListView(LoginRequiredMixin, ListView):
    model = Journal
    template_name = 'accounting/journal_list.html'
    context_object_name = 'journals'
    paginate_by = 20

    def get_queryset(self):
        return Journal.objects.filter(organization=self.request.user.organization).order_by('-journal_date')

class JournalCreateView(LoginRequiredMixin, CreateView):
    model = Journal
    form_class = JournalForm
    template_name = 'accounting/journal_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = JournalLineFormSet(self.request.POST)
        else:
            context['lines'] = JournalLineFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        
        with transaction.atomic():
            form.instance.organization = self.request.user.organization
            form.instance.created_by = self.request.user
            self.object = form.save()
            
            if lines.is_valid():
                lines.instance = self.object
                lines.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('journal_detail', kwargs={'pk': self.object.pk})

class JournalUpdateView(LoginRequiredMixin, UpdateView):
    model = Journal
    form_class = JournalForm
    template_name = 'accounting/journal_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = JournalLineFormSet(self.request.POST, instance=self.object)
        else:
            context['lines'] = JournalLineFormSet(instance=self.object)
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
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('journal_detail', kwargs={'pk': self.object.pk})

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

# HTMX Partial Views
class HTMXJournalLineFormView(LoginRequiredMixin, View):
    def get(self, request):
        form = JournalLineForm(organization=request.user.organization)
        return render(request, 'accounting/partials/journal_line_form.html', {'form': form})

class HTMXAccountAutocompleteView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('query', '')
        accounts = ChartOfAccount.objects.filter(
            organization=request.user.organization,
            account_code__icontains=query
        )[:10]
        results = [{'id': a.account_id, 'text': f"{a.account_code} - {a.account_name}"} for a in accounts]
        return JsonResponse({'results': results})

# Voucher Mode Views
class VoucherModeConfigListView(LoginRequiredMixin, ListView):
    model = VoucherModeConfig
    template_name = 'accounting/voucher_config_list.html'
    context_object_name = 'configs'
    
    def get_queryset(self):
        return VoucherModeConfig.objects.filter(organization=self.request.user.organization)

class VoucherModeConfigCreateView(LoginRequiredMixin, CreateView):
    model = VoucherModeConfig
    form_class = VoucherModeConfigForm
    template_name = 'accounting/voucher_config_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('voucher_config_detail', kwargs={'pk': self.object.pk})

class VoucherModeConfigUpdateView(LoginRequiredMixin, UpdateView):
    model = VoucherModeConfig
    form_class = VoucherModeConfigForm
    template_name = 'accounting/voucher_config_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('voucher_config_detail', kwargs={'pk': self.object.pk})

class VoucherModeConfigDetailView(LoginRequiredMixin, DetailView):
    model = VoucherModeConfig
    template_name = 'accounting/voucher_config_detail.html'
    context_object_name = 'config'

class VoucherModeDefaultCreateView(LoginRequiredMixin, CreateView):
    model = VoucherModeDefault
    form_class = VoucherModeDefaultForm
    template_name = 'accounting/voucher_default_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        kwargs['config_id'] = self.kwargs['config_id']
        return kwargs
    
    def form_valid(self, form):
        config = get_object_or_404(VoucherModeConfig, pk=self.kwargs['config_id'])
        form.instance.config = config
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('voucher_config_detail', kwargs={'pk': self.kwargs['config_id']})

class VoucherModeDefaultUpdateView(LoginRequiredMixin, UpdateView):
    model = VoucherModeDefault
    form_class = VoucherModeDefaultForm
    template_name = 'accounting/voucher_default_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        kwargs['config_id'] = self.object.config_id
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('voucher_config_detail', kwargs={'pk': self.object.config_id})

class VoucherModeDefaultDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        default = get_object_or_404(VoucherModeDefault, pk=pk)
        config_id = default.config_id
        default.delete()
        return redirect('voucher_config_detail', pk=config_id)

class VoucherEntryView(LoginRequiredMixin, View):
    template_name = 'accounting/voucher_entry.html'
    
    def get(self, request, config_id=None):
        if config_id:
            config = get_object_or_404(VoucherModeConfig, pk=config_id, organization=request.user.organization)
        else:
            config = VoucherModeConfig.objects.filter(
                organization=request.user.organization,
                is_default=True
            ).first()
        
        if not config:
            return redirect('voucher_config_list')
        
        journal_form = JournalForm(organization=request.user.organization, initial={
            'journal_type': config.journal_type,
            'currency_code': config.default_currency,
        })
        
        defaults = config.defaults.all().order_by('display_order')
        
        context = {
            'config': config,
            'journal_form': journal_form,
            'defaults': defaults,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, config_id=None):
        config = get_object_or_404(VoucherModeConfig, pk=config_id, organization=request.user.organization)
        
        journal_form = JournalForm(request.POST, organization=request.user.organization)
        line_forms = []
        
        if journal_form.is_valid():
            with transaction.atomic():
                journal = journal_form.save(commit=False)
                journal.organization = request.user.organization
                journal.created_by = request.user
                journal.save()
                
                for default in config.defaults.all().order_by('display_order'):
                    account = default.account
                    if not account:
                        continue
                    
                    debit_amount = default.default_amount if default.default_debit else 0
                    credit_amount = default.default_amount if default.default_credit else 0
                    
                    JournalLine.objects.create(
                        journal=journal,
                        line_number=default.display_order,
                        account=account,
                        description=default.default_description or '',
                        debit_amount=debit_amount,
                        credit_amount=credit_amount,
                        currency_code=journal.currency_code,
                        exchange_rate=journal.exchange_rate,
                        functional_debit_amount=debit_amount * journal.exchange_rate,
                        functional_credit_amount=credit_amount * journal.exchange_rate,
                        department=default.default_department,
                        project=default.default_project,
                        cost_center=default.default_cost_center,
                        tax_code=default.default_tax_code,
                        created_by=request.user,
                    )
                
                return redirect('journal_detail', pk=journal.pk)
        
        defaults = config.defaults.all().order_by('display_order')
        
        context = {
            'config': config,
            'journal_form': journal_form,
            'defaults': defaults,
        }
        
        return render(request, self.template_name, context)