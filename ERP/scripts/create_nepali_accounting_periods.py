import os
# import sys
# sys.path.append('/dashboard')
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard.settings")
django.setup()

from accounting.models import FiscalYear, AccountingPeriod
from nepali_datetime import date as nep_date, NepaliDate
from datetime import timedelta

# Nepali months in order
NEPALI_MONTHS = [
    "Baisakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

def create_nepali_accounting_periods(fiscal_year_code, organization):
    fy = FiscalYear.objects.get(code=fiscal_year_code, organization=organization)
    # Convert start_date to Nepali date
    nep_start = NepaliDate.from_datetime_date(fy.start_date)
    periods = []
    for i, nep_month in enumerate(NEPALI_MONTHS):
        # Get start of month
        if i == 0:
            period_start = nep_start
        else:
            period_start = NepaliDate(nep_start.year, i+1, 1)
        # Get end of month
        if i < 11:
            next_month_start = NepaliDate(nep_start.year, i+2, 1)
            period_end = next_month_start - timedelta(days=1)
        else:
            # Last month: set end as fiscal year end
            period_end = NepaliDate.from_datetime_date(fy.end_date)
        # Convert back to Gregorian
        start_greg = period_start.to_datetime_date()
        end_greg = period_end.to_datetime_date()
        # Create or update period
        ap, created = AccountingPeriod.objects.get_or_create(
            fiscal_year=fy,
            period_number=i+1,
            defaults={
                "name": f"{nep_month} {fy.name}",
                "start_date": start_greg,
                "end_date": end_greg,
                "status": "open",
                "is_current": (i == 0)
            }
        )
        periods.append(ap)
        print(f"{'Created' if created else 'Exists'}: {ap.name} ({start_greg} - {end_greg})")
    return periods

if __name__ == "__main__":
    # Example usage: replace with your org instance or id
    from usermanagement.models import Organization
    org = Organization.objects.first()
    create_nepali_accounting_periods("2081-2082", org)
