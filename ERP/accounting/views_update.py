from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .views_mixins import UserOrganizationMixin, PermissionRequiredMixin
from .models import *
from .forms import *
from django.urls import reverse, reverse_lazy
from django.contrib import messages  # Add this import for messages
from django.db import transaction    # Add this import for transaction
from django.shortcuts import get_object_or_404  # Add this import for get_object_or_404

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
            'config_id': self.object.config_id,
            'form_title': f'Update Default Line for {config.name}',
            'page_title': f'Update Default Line: {config.name}',
            'breadcrumbs': [
                ('Voucher Configurations', reverse('accounting:voucher_config_list')),
                (f'{config.name} Details', reverse('accounting:voucher_config_detail', kwargs={'pk': config.pk})),
                ('Update Default Line', None)
            ]
        })
        return context