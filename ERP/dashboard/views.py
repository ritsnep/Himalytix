from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Sum, Q
from decimal import Decimal

from accounting.models import (
    ChartOfAccount, Journal, JournalLine, GeneralLedger,
    FiscalYear, AccountingPeriod, AccountType
)
from usermanagement.models import Organization

# Dashboard
# @login_required
# class DashboardView(View):
#     def get(self, request):
#         return render(request, "dashboard.html")

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        organization = user.get_active_organization()
        
        if not organization:
            context['error'] = 'No active organization found. Please select an organization.'
            return context
        
        # Get current fiscal year and period
        current_fiscal_year = FiscalYear.objects.filter(
            organization_id=organization.id,
            is_current=True
        ).first()
        
        current_period = None
        if current_fiscal_year:
            current_period = AccountingPeriod.objects.filter(
                fiscal_year_id=current_fiscal_year.id,
                is_current=True
            ).first()
        
        # Get account balances
        account_balances = self.get_account_balances(organization, current_period)
        
        # Get recent journals
        recent_journals = Journal.objects.filter(
            organization_id=organization.id
        ).order_by('-journal_date', '-created_at')[:10]
        
        # Get financial summary
        financial_summary = self.get_financial_summary(organization, current_period)
        
        context.update({
            'organization': organization,
            'current_fiscal_year': current_fiscal_year,
            'current_period': current_period,
            'account_balances': account_balances,
            'recent_journals': recent_journals,
            'financial_summary': financial_summary,
        })
        
        return context
    
    def get_account_balances(self, organization, period):
        """Get account balances for the dashboard"""
        if not period:
            return []
        
        # Get account balances from GeneralLedger
        balances = GeneralLedger.objects.filter(
            organization_id=organization.id,
            period=period
        ).values('account__account_name', 'account__account_code').annotate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        ).order_by('account__account_code')[:10]  # Top 10 accounts
        
        for balance in balances:
            balance['net_balance'] = (balance['total_debit'] or Decimal('0')) - (balance['total_credit'] or Decimal('0'))
        
        return balances
    
    def get_financial_summary(self, organization, period):
        """Get key financial metrics"""
        if not period:
            return {}
        
        # Get total assets, liabilities, equity
        asset_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='asset'
        )
        liability_accounts = ChartOfAccount.objects.filter(
            organization_id=organization.id,
            account_type__nature='liability'
        )
        equity_accounts = ChartOfAccount.objects.filter(
            organization=organization,
            account_type__nature='equity'
        )
        
        # Calculate totals (simplified - you might want to use GeneralLedger for actual balances)
        total_assets = Decimal('0')
        total_liabilities = Decimal('0')
        total_equity = Decimal('0')
        
        # Get total journals for the period
        total_journals = Journal.objects.filter(
            organization=organization,
            period=period
        ).count()
        
        # Get posted vs draft journals
        posted_journals = Journal.objects.filter(
            organization=organization,
            period=period,
            status='posted'
        ).count()
        
        draft_journals = Journal.objects.filter(
            organization=organization,
            period=period,
            status='draft'
        ).count()
        
        return {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'total_journals': total_journals,
            'posted_journals': posted_journals,
            'draft_journals': draft_journals,
        }

class Settings(LoginRequiredMixin, View):
    template_name = "settings.html"

    def __init__(self, *args):
        super(Settings, self).__init__(*args)

    def get(self, request):
        return render(request, self.template_name)


