# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Journal URLs
    path('journals/', views.JournalListView.as_view(), name='journal_list'),
    path('journals/create/', views.JournalCreateView.as_view(), name='journal_create'),
    path('journals/<int:pk>/', views.JournalDetailView.as_view(), name='journal_detail'),
    path('journals/<int:pk>/edit/', views.JournalUpdateView.as_view(), name='journal_update'),
    path('journals/<int:pk>/post/', views.JournalPostView.as_view(), name='journal_post'),
    
    # HTMX Partial URLs
    path('htmx/journal-line-form/', views.HTMXJournalLineFormView.as_view(), name='htmx_journal_line_form'),
    path('htmx/account-autocomplete/', views.HTMXAccountAutocompleteView.as_view(), name='htmx_account_autocomplete'),
    
    # Voucher Mode URLs
    path('voucher-configs/', views.VoucherModeConfigListView.as_view(), name='voucher_config_list'),
    path('voucher-configs/create/', views.VoucherModeConfigCreateView.as_view(), name='voucher_config_create'),
    path('voucher-configs/<int:pk>/', views.VoucherModeConfigDetailView.as_view(), name='voucher_config_detail'),
    path('voucher-configs/<int:pk>/edit/', views.VoucherModeConfigUpdateView.as_view(), name='voucher_config_update'),
    
    path('voucher-configs/<int:config_id>/defaults/create/', views.VoucherModeDefaultCreateView.as_view(), name='voucher_default_create'),
    path('voucher-defaults/<int:pk>/edit/', views.VoucherModeDefaultUpdateView.as_view(), name='voucher_default_update'),
    path('voucher-defaults/<int:pk>/delete/', views.VoucherModeDefaultDeleteView.as_view(), name='voucher_default_delete'),
    
    path('voucher-entry/', views.VoucherEntryView.as_view(), name='voucher_entry'),
    path('voucher-entry/<int:config_id>/', views.VoucherEntryView.as_view(), name='voucher_entry_config'),
]