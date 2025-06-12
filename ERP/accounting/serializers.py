from rest_framework import serializers
from .models import VoucherModeConfig

class VoucherModeConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoucherModeConfig
        fields = [
            'layout_style',
            'show_account_balances',
            'show_tax_details',
            'show_dimensions',
            'allow_multiple_currencies',
            'require_line_description',
        ]