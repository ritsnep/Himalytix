from rest_framework import viewsets, renderers
import csv
import logging
from io import TextIOWrapper
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounting.models import FiscalYear
from .serializers import FiscalYearSerializer
from rest_framework.response import Response
from rest_framework import status
from accounting.models import ChartOfAccount, Journal, CurrencyExchangeRate
from accounting.services import post_journal, close_period, get_trial_balance
from .serializers import (
    ChartOfAccountSerializer,
    JournalSerializer,
    CurrencyExchangeRateSerializer,
)
from .permissions import IsOrganizationMember

logger = logging.getLogger(__name__)

class BaseOrgViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    renderer_classes = [renderers.JSONRenderer, renderers.BrowsableAPIRenderer]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

class ChartOfAccountViewSet(BaseOrgViewSet):
    queryset = ChartOfAccount.objects.all()
    serializer_class = ChartOfAccountSerializer

    def get_queryset(self):
        return super().get_queryset().select_related("parent_account", "account_type")

class JournalViewSet(BaseOrgViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer

    def get_queryset(self):
        return super().get_queryset().select_related("journal_type", "period").prefetch_related("lines__account")

    def perform_create(self, serializer):
        journal = serializer.save(organization=self.request.user.organization)
        post_journal(journal)

class CurrencyExchangeRateViewSet(BaseOrgViewSet):
    queryset = CurrencyExchangeRate.objects.all()
    serializer_class = CurrencyExchangeRateSerializer

    def get_queryset(self):
        return super().get_queryset().select_related("from_currency", "to_currency")

class JournalImportView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    renderer_classes = [renderers.JSONRenderer, renderers.BrowsableAPIRenderer]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        reader = csv.DictReader(TextIOWrapper(file, encoding="utf-8"))
        created = []
        for row in reader:
            serializer = JournalSerializer(data=row)
            if serializer.is_valid():
                journal = serializer.save(organization=request.user.organization)
                post_journal(journal)
                created.append(journal.journal_id)
            else:
                logger.debug("Invalid row: %s", serializer.errors)
        return Response({"created": created})


class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    renderer_classes = [renderers.JSONRenderer, renderers.BrowsableAPIRenderer]

    def get(self, request):
        fiscal_year = request.query_params.get("fiscal_year")
        if not fiscal_year:
            return Response({"detail": "fiscal_year parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            fy = FiscalYear.objects.get(pk=fiscal_year, organization=request.user.organization)
        except FiscalYear.DoesNotExist:
            raise Http404

        data = get_trial_balance(request.user.organization, fy)
        return Response({"results": data})