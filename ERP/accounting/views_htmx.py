from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from .views_mixins import VoucherConfigMixin

class LineRowHXView(LoginRequiredMixin, VoucherConfigMixin, View):
    def get(self, request, *a, **kw):
        _, LineFS = self.get_forms()
        form = LineFS().empty_form   # generates one blank row
        return render(request, "accounting/partials/voucher_form_line_row.html", {"form": form}) 