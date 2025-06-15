from django.db import transaction
from django.utils import timezone
from models.fiscal_year import FiscalYear
from models.accounting_period import AccountingPeriod
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class FiscalYearService:
    @staticmethod
    @transaction.atomic
    def create_fiscal_year(organization, data, created_by):
        fiscal_year = FiscalYear(
            organization=organization,
            created_by=created_by,
            **data
        )
        fiscal_year.save()
        
        # Create accounting periods
        FiscalYearService._create_accounting_periods(fiscal_year)
        return fiscal_year

    @staticmethod
    def _create_accounting_periods(fiscal_year):
        # Create standard monthly periods
        current_date = fiscal_year.start_date
        while current_date < fiscal_year.end_date:
            end_date = min(
                current_date.replace(day=28) + timezone.timedelta(days=4),
                fiscal_year.end_date
            )
            
            AccountingPeriod.objects.create(
                organization=fiscal_year.organization,
                fiscal_year=fiscal_year,
                name=current_date.strftime("%B %Y"),
                start_date=current_date,
                end_date=end_date,
                is_closed=False,
                created_by=fiscal_year.created_by
            )
            
            current_date = end_date + timezone.timedelta(days=1)

    @staticmethod
    @transaction.atomic
    def close_fiscal_year(fiscal_year, closed_by):
        if fiscal_year.status != 'active':
            raise ValidationError(_("Only active fiscal years can be closed"))

        # Generate closing entries
        FiscalYearService._generate_closing_entries(fiscal_year, closed_by)
        
        # Close all periods
        AccountingPeriod.objects.filter(
            fiscal_year=fiscal_year
        ).update(is_closed=True)
        
        # Update fiscal year status
        fiscal_year.status = 'closed'
        fiscal_year.closed_by = closed_by
        fiscal_year.closed_at = timezone.now()
        fiscal_year.save()

    @staticmethod
    def _generate_closing_entries(fiscal_year, closed_by):
        # Implementation for generating closing entries
        # This would integrate with your journal entry system
        pass 