from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from services.fiscal_year_service import FiscalYearService

@login_required
def create_fiscal_year(request):
    if not request.user.has_perm('accounting.add_fiscalyear'):
        raise PermissionDenied

    if request.method == 'POST':
        try:
            fiscal_year = FiscalYearService.create_fiscal_year(
                organization=request.user.organization,
                data=request.POST,
                created_by=request.user
            )
            return JsonResponse({'status': 'success', 'id': fiscal_year.id})
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def close_fiscal_year(request, fiscal_year_id):
    if not request.user.has_perm('accounting.change_fiscalyear'):
        raise PermissionDenied

    fiscal_year = get_object_or_404(FiscalYear, id=fiscal_year_id)
    
    if request.method == 'POST':
        try:
            FiscalYearService.close_fiscal_year(fiscal_year, request.user)
            return JsonResponse({'status': 'success'})
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}) 