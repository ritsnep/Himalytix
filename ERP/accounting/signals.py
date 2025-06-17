from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import JournalType, VoucherModeConfig, VoucherModeDefault

@receiver(post_save, sender=JournalType)
def create_default_voucher_config(sender, instance, created, **kwargs):
    """Automatically create a VoucherModeConfig for new journal types."""
    if not created:
        return

    VoucherModeConfig.objects.get_or_create(
        organization=instance.organization,
        journal_type=instance,
        is_default=True,
        defaults={
            "name": f"Default Config for {instance.name}",
            # 'code' will be generated in model.save()
            "layout_style": "standard",
            "show_account_balances": True,
            "show_tax_details": True,
            "show_dimensions": True,
            "allow_multiple_currencies": False,
            "require_line_description": True,
            "default_currency": getattr(instance.organization, "base_currency_code", "USD"),
        },
    )