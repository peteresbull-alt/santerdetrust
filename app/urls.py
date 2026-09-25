"""
URL configuration for banking app
"""
from django.urls import path
from app import auth_views, views, api_views



urlpatterns = [

    # ============================================
    # LANDING PAGES
    # ============================================
    path('', views.landing_home, name='landing_home'),
    # ============================================
    # AUTHENTICATION URLS
    # ============================================
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    
    # ============================================
    # DASHBOARD
    # ============================================
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # ============================================
    # ACCOUNT URLS
    # ============================================
    path('accounts/', views.account_list_view, name='account_list'),
    path('accounts/<str:account_number>/', views.account_detail_view, name='account_detail'),
    path('accounts/apply/new/', views.account_apply_view, name='account_apply'),
    path('accounts/<str:account_number>/activate/', views.account_activate_view, name='account_activate'),
    
    # ============================================
    # CARD URLS
    # ============================================
    path('cards/', views.card_list_view, name='card_list'),
    path('cards/<int:card_id>/', views.card_detail_view, name='card_detail'),
    path('cards/apply/new/', views.card_apply_view, name='card_apply'),
    path('cards/<int:card_id>/activate/', views.card_activate_view, name='card_activate'),
    path('cards/<int:card_id>/block/', views.card_block_view, name='card_block'),
    
    # ============================================
    # TRANSACTION URLS
    # ============================================
    path('transactions/deposit/', views.deposit_view, name='deposit'),
    path('transactions/withdrawal/', views.withdrawal_view, name='withdrawal'),
    path('transactions/', views.transaction_list_view, name='transaction_list'),
    path('transactions/<str:transaction_id>/', views.transaction_detail_view, name='transaction_detail'),
    
    
    
    # ============================================
    # TRANSFER URLS
    # ============================================
    path('transfer/', views.transfer_view, name='transfer'),
    path('transfer/validate-tac/', views.validate_tac_view, name='validate_tac'),
    
    # ============================================
    # BENEFICIARY URLS
    # ============================================
    path('beneficiaries/', views.beneficiary_list_view, name='beneficiary_list'),
    path('beneficiaries/add/', views.beneficiary_add_view, name='beneficiary_add'),
    path('beneficiaries/<int:beneficiary_id>/edit/', views.beneficiary_edit_view, name='beneficiary_edit'),
    path('beneficiaries/<int:beneficiary_id>/delete/', views.beneficiary_delete_view, name='beneficiary_delete'),
    
    # ============================================
    # PROFILE URLS
    # ============================================
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/employment/', views.employment_info_view, name='employment_info'),
    path('profile/kyc/', views.kyc_documents_view, name='kyc_documents'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    
    # ============================================
    # NOTIFICATION URLS
    # ============================================
    path('notifications/', views.notification_list_view, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read_view, name='notification_mark_all_read'),
    
    # ============================================
    # SUPPORT TICKET URLS
    # ============================================
    path('support/', views.support_ticket_list_view, name='support_ticket_list'),
    path('support/create/', views.support_ticket_create_view, name='support_ticket_create'),
    path('support/<str:ticket_number>/', views.support_ticket_detail_view, name='support_ticket_detail'),
]