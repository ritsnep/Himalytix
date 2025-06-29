from django.contrib import admin
from .models import (
    FiscalYear, AccountingPeriod, Department, Project, CostCenter, AccountType,
    ChartOfAccount, Currency, CurrencyExchangeRate, JournalType, Journal, JournalLine,
    TaxAuthority, TaxType, TaxCode, VoucherModeConfig, VoucherModeDefault, GeneralLedger
)

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('journal_number', 'journal_type', 'period', 'status', 'created_at')
    search_fields = ('journal_number', 'description')
    list_filter = ('journal_type', 'status', 'period')

admin.site.register(FiscalYear)
admin.site.register(AccountingPeriod)
admin.site.register(Department)
admin.site.register(Project)
admin.site.register(CostCenter)
admin.site.register(AccountType)
admin.site.register(ChartOfAccount)
admin.site.register(Currency)
admin.site.register(CurrencyExchangeRate)
admin.site.register(JournalType)
admin.site.register(JournalLine)
admin.site.register(TaxAuthority)
admin.site.register(TaxType)
admin.site.register(TaxCode)
admin.site.register(VoucherModeConfig)
admin.site.register(VoucherModeDefault)
admin.site.register(GeneralLedger)