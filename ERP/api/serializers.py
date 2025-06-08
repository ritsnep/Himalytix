from rest_framework import serializers
from accounting.models import FiscalYear


class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = [
            'fiscal_year_id',
            'organization',
            'code',
            'name',
            'start_date',
            'end_date',
            'status',
            'is_current',
        ]