import logging
from dataclasses import dataclass
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Journal, JournalType, JournalLine, AccountingPeriod, GeneralLedger

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
    if journal.total_debit != journal.total_credit:
        raise ValidationError("Journal not balanced")
    with transaction.atomic():
        if journal.period.status != "open":
            raise ValidationError("Accounting period is closed")
        jt = JournalType.objects.select_for_update().get(pk=journal.journal_type.pk)
        if not journal.journal_number:
            prefix = jt.auto_numbering_prefix or ""
            suffix = jt.auto_numbering_suffix or ""
            number = jt.auto_numbering_next
            journal.journal_number = f"{prefix}{number}{suffix}"
            jt.auto_numbering_next = number + 1
            jt.save()
        for line in journal.lines.select_related("account"):
            balance_after = line.account.current_balance + (line.debit_amount - line.credit_amount)
            GeneralLedger.objects.create(
                organization_id=journal.organization,
                account=line.account,
                journal=journal,
                journal_line=line,
                period=journal.period,
                transaction_date=journal.journal_date,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                balance_after=balance_after,
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
            line.account.current_balance = balance_after
            line.account.save(update_fields=["current_balance"])
        journal.status = "posted"
        journal.posted_at = timezone.now()
        journal.save(update_fields=["status", "posted_at", "journal_number"])
    logger.info("post_journal end journal_id=%s", journal.pk)
    return journal


def close_period(period: AccountingPeriod, user) -> AccountingPeriod:
    """Close an accounting period."""
    logger.info("close_period start period_id=%s", period.pk)
    with transaction.atomic():
        for j in period.journal_set.select_related("journal_type"):
            if j.status != "posted":
                raise ValidationError("All journals must be posted before closing")
            if j.total_debit != j.total_credit:
                raise ValidationError("Unbalanced journal exists")
        period.status = "closed"
        period.closed_at = timezone.now()
        period.closed_by = user
        period.save(update_fields=["status", "closed_at", "closed_by"])
    logger.info("close_period end period_id=%s", period.pk)
    return period