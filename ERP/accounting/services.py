import logging
from dataclasses import dataclass
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import (
    Journal, JournalType, JournalLine, AccountingPeriod,
    GeneralLedger, VoucherModeConfig, ChartOfAccount, FiscalYear, Organization
)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class JournalPostParams:
    journal: Journal

@dataclass(frozen=True)
class PeriodCloseParams:
    period: AccountingPeriod
    user: object


def post_journal(journal: Journal) -> Journal:
    """Post a draft journal and create GL entries."""
    logger.info("post_journal start journal_id=%s", journal.pk)
    if journal.status != "draft":
        raise ValidationError("Only draft journals can be posted")
    line_totals = journal.lines.aggregate(
        debit_sum=Sum("debit_amount"),
        credit_sum=Sum("credit_amount"),
    )
    debit_sum = line_totals.get("debit_sum") or Decimal("0")
    credit_sum = line_totals.get("credit_sum") or Decimal("0")

    if debit_sum != credit_sum or journal.total_debit != journal.total_credit:
        raise ValidationError("Journal not balanced")

    if debit_sum != journal.total_debit or credit_sum != journal.total_credit:
        raise ValidationError("Header totals do not match line totals")
    with transaction.atomic():
        if journal.period.status != "open":
            raise ValidationError("Accounting period is closed")

        jt = JournalType.objects.select_for_update().get(pk=journal.journal_type.pk)
        if not journal.journal_number:
            journal.journal_number = jt.get_next_journal_number(journal.period)

        journal.save()

        for line in journal.lines.select_related("account").all():
            line.functional_debit_amount = line.debit_amount * journal.exchange_rate
            line.functional_credit_amount = line.credit_amount * journal.exchange_rate
            line.save()

            account = line.account
            account.current_balance = account.current_balance + line.debit_amount - line.credit_amount
            account.save(update_fields=["current_balance"])

            GeneralLedger.objects.create(
                organization_id=journal.organization,
                account=account,
                journal=journal,
                journal_line=line,
                period=journal.period,
                transaction_date=journal.journal_date,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                balance_after=account.current_balance,
                currency_code=line.currency_code,
                exchange_rate=line.exchange_rate,
                functional_debit_amount=line.functional_debit_amount,
                functional_credit_amount=line.functional_credit_amount,
                department=line.department,
                project=line.project_id,
                cost_center=line.cost_center,
                description=line.description,
                source_module=journal.source_module,
                source_reference=journal.source_reference,
            )

        journal.status = "posted"
        journal.posted_at = timezone.now()
        journal.save()
    return journal
def post_journal_with_params(params: JournalPostParams) -> Journal:
    """Post a journal using parameters."""
    journal = params.journal
    if journal.status != "draft":
        raise ValidationError("Only draft journals can be posted")
    line_totals = journal.lines.aggregate(
        debit_sum=Sum("debit_amount"),
        credit_sum=Sum("credit_amount"),
    )
    debit_sum = line_totals.get("debit_sum") or Decimal("0")
    credit_sum = line_totals.get("credit_sum") or Decimal("0")

    if debit_sum != credit_sum or journal.total_debit != journal.total_credit:
        raise ValidationError("Journal not balanced")

    if debit_sum != journal.total_debit or credit_sum != journal.total_credit:
        raise ValidationError("Header totals do not match line totals")
    with transaction.atomic():
        if journal.period.status != "open":
            raise ValidationError("Accounting period is closed")
        jt = JournalType.objects.select_for_update().get(pk=journal.journal_type.pk)
        if not journal.journal_number:
            journal.journal_number = jt.get_next_journal_number(journal.period)

        journal.save()

        for line in journal.lines.select_related("account").all():
            acc = line.account
            if acc.require_department and not line.department:
                raise ValidationError(f"Department required for account {acc.account_code}")
            if acc.require_project and not line.project_id:
                raise ValidationError(f"Project required for account {acc.account_code}")
            if acc.require_cost_center and not line.cost_center:
                raise ValidationError(f"Cost center required for account {acc.account_code}")

            line.functional_debit_amount = line.debit_amount * journal.exchange_rate
            line.functional_credit_amount = line.credit_amount * journal.exchange_rate
            line.save()

            acc = line.account
            acc.current_balance = acc.current_balance + line.debit_amount - line.credit_amount
            acc.save(update_fields=["current_balance"])

            GeneralLedger.objects.create(
                organization_id=journal.organization,
                account=acc,
                journal=journal,
                journal_line=line,
                period=journal.period,
                transaction_date=journal.journal_date,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                balance_after=acc.current_balance,
                currency_code=line.currency_code,
                exchange_rate=line.exchange_rate,
                functional_debit_amount=line.functional_debit_amount,
                functional_credit_amount=line.functional_credit_amount,
                department=line.department,
                project=line.project_id,
                cost_center=line.cost_center,
                description=line.description,
                source_module=journal.source_module,
                source_reference=journal.source_reference,
            )

        journal.status = "posted"
        journal.posted_at = timezone.now()
        journal.save()
    return journal



def create_voucher(user, config_id: int, header_data: dict, lines_data: list):
    """
    Create a voucher (journal) and its lines.
    """
    # Example implementation, adjust as needed
    from .models import VoucherModeConfig

    config = VoucherModeConfig.objects.get(pk=config_id)
    journal = Journal(
        organization=user.organization,
        created_by=user,
        journal_type=config.journal_type,
        **header_data
    )
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    lines = []
    for idx, line in enumerate(lines_data, start=1):
        account = ChartOfAccount.objects.get(pk=line['account'])
        debit = Decimal(line.get('debit_amount', 0) or 0)
        credit = Decimal(line.get('credit_amount', 0) or 0)
        total_debit += debit
        total_credit += credit
        lines.append(JournalLine(
            journal=journal,
            line_number=idx,
            account=account,
            description=line.get('description', ''),
            debit_amount=debit,
            credit_amount=credit,
            department_id=line.get('department'),
            project_id=line.get('project'),
            cost_center_id=line.get('cost_center'),
            tax_code_id=line.get('tax_code'),
            memo=line.get('memo', ''),
            currency_code=journal.currency_code,
            exchange_rate=journal.exchange_rate,
        ))

    if total_debit != total_credit:
        raise ValidationError('Debit and Credit totals must match')

    journal.total_debit = total_debit
    journal.total_credit = total_credit

    with transaction.atomic():
        journal.save()
        JournalLine.objects.bulk_create(lines)

    return journal


def get_trial_balance(organization: Organization, fiscal_year: FiscalYear):
    """Return trial balance data for an organization and fiscal year."""
    qs = (
        GeneralLedger.objects.filter(
            organization_id=organization,
            period__fiscal_year=fiscal_year,
            is_archived=False,
        )
        .values(
            "account_id",
            "account__account_code",
            "account__account_name",
        )
        .annotate(
            debit_total=Sum("debit_amount"),
            credit_total=Sum("credit_amount"),
        )
        .order_by("account__account_code")
    )

    results = []
    for row in qs:
        balance = (row["debit_total"] or Decimal("0")) - (row["credit_total"] or Decimal("0"))
        results.append(
            {
                "account_id": row["account_id"],
                "account_code": row["account__account_code"],
                "account_name": row["account__account_name"],
                "debit_total": row["debit_total"] or Decimal("0"),
                "credit_total": row["credit_total"] or Decimal("0"),
                "balance": balance,
            }
        )
    return results

def close_period(period: AccountingPeriod, user=None):
    """
    Close an accounting period.
    """
    if period.status != "open":
        raise ValidationError("Only open periods can be closed")
    period.status = "closed"
    period.closed_by = user if hasattr(period, "closed_by") else None
    period.closed_at = timezone.now() if hasattr(period, "closed_at") else None
    period.save()
    logger.info("Closed period %s by user %s", period.pk, getattr(user, "pk", None))
    return period