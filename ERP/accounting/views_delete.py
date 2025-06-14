from .models import *
from .forms import *
from django.views.generic import DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .views_mixins import UserOrganizationMixin, PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator  # Add this import for method_decorator
from usermanagement.utils import require_permission   # Add this import for require_permission

class VoucherModeDefaultDeleteView(LoginRequiredMixin, View):
    @method_decorator(require_permission('accounting','vouchermodedefault','delete'))
    def post(self, request, pk):
        default = get_object_or_404(VoucherModeDefault, pk=pk, config__organization=request.user.get_active_organization())
        config_id = default.config_id
        default.delete()
        messages.success(request, "Voucher default line deleted successfully.")
        return redirect(reverse_lazy('accounting:voucher_config_detail', kwargs={'pk': config_id}))

# Add other DeleteView classes here as needed