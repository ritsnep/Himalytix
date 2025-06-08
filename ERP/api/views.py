from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounting.models import FiscalYear
from .serializers import FiscalYearSerializer


class FiscalYearViewSet(viewsets.ModelViewSet):
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer
    permission_classes = [IsAuthenticated]