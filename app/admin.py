from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import (
    Account,
    Beneficiary,
    AuditLog,
    Card,
    ExchangeRate,
    Loan,
    Notification,
    LoanRepayment,
    SupportTicket,
    CustomUser,
    Transaction,
    DepositDetails,
)


class CustomUserCreationForm(UserCreationForm):
    """Admin 'add user' form. UserCreationForm.save() calls set_password(),
    so the password is always hashed instead of stored as typed."""

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number')


class CustomUserChangeForm(UserChangeForm):
    """Admin 'edit user' form. Renders the password field as a read-only
    hash + 'change password' link rather than an editable text box."""

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = (
        'email', 'first_name', 'last_name', 'phone_number',
        'account_status', 'is_staff', 'is_active', 'date_joined',
    )
    list_filter = ('is_staff', 'is_active', 'account_status', 'has_verified_kyc', 'can_receive_tac_mail')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'bank_id', 'customer_id')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('password_changed_at',)

    # Fields shown when adding a user through the admin ("+ Add user") 
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2'),
        }),
    )

    # Fields shown when editing an existing user
    fieldsets = (
        ('Login Credentials', {
            'fields': ('email', 'password'),
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'plantext_plain', 'phone_number', 'alternate_phone',
                'date_of_birth', 'gender', 'marital_status', 'number_of_dependents', 'nationality',
            ),
        }),
        ('Identifiers', {
            'fields': ('bank_id', 'customer_id', 'ssn', 'tax_identity_number'),
        }),
        ('Address', {
            'fields': ('address', 'address_line2', 'city', 'state', 'country', 'postal_code'),
        }),
        ('Citizenship', {
            'fields': ('citizenship_status',),
        }),
        ('Employment', {
            'fields': (
                'employment_status', 'employer_name', 'employer_phone', 'employer_address',
                'employment_type', 'job_title', 'job_start_date', 'job_end_date', 'annual_income',
            ),
            'classes': ('collapse',),
        }),
        ('Government ID', {
            'fields': (
                'government_id_type', 'government_id_number', 'government_id_expiry',
                'front_id_image', 'back_id_image',
            ),
            'classes': ('collapse',),
        }),
        ('Documents', {
            'fields': ('proof_of_employment', 'proof_of_income', 'proof_of_address', 'profile_image'),
            'classes': ('collapse',),
        }),
        ('Preferences', {
            'fields': ('preferred_currency', 'preferred_language'),
        }),
        ('Account Status & Limits', {
            'fields': (
                'account_status', 'can_apply_for_loans', 'can_apply_for_cards', 'can_make_transfers',
                'daily_transfer_limit', 'monthly_transfer_limit',
            ),
        }),
        ('Transfer Authorization Code (TAC)', {
            'fields': ('tac', 'tac_generated_at', 'can_receive_tac_mail'),
        }),
        ('KYC', {
            'fields': ('has_submitted_kyc', 'has_verified_kyc', 'kyc_verified_at', 'kyc_verified_by'),
        }),
        ('Security', {
            'fields': (
                'two_factor_enabled', 'two_factor_method',
                'failed_login_attempts', 'account_locked_until', 'password_changed_at', 'last_login_ip',
            ),
            'classes': ('collapse',),
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_reason'),
            'classes': ('collapse',),
        }),
        ('Referral', {
            'fields': ('referred_by', 'referral_code'),
            'classes': ('collapse',),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'email_verified', 'phone_verified', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'last_activity'),
        }),
    )


# Register your models here.
admin.site.register(Account)
admin.site.register(Beneficiary)
admin.site.register(Card)
admin.site.register(ExchangeRate)
admin.site.register(Loan)
admin.site.register(LoanRepayment)
admin.site.register(Notification)
admin.site.register(SupportTicket)
admin.site.register(AuditLog)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'user_email', 'transaction_type', 'amount', 'currency',
        'status', 'channel', 'initiated_at',
    )
    list_filter = ('transaction_type', 'status', 'channel', 'currency')
    search_fields = (
        'transaction_id', 'user__email', 'account__account_number',
        'beneficiary_name', 'reference_number',
    )
    ordering = ('-initiated_at',)
    date_hierarchy = 'initiated_at'

    @admin.display(description='User Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email


@admin.register(DepositDetails)
class DepositDetailsAdmin(admin.ModelAdmin):
    list_display = ['label', 'payment_method', 'user', 'is_active', 'created_at']
    list_filter = ['payment_method', 'is_active']
    list_editable = ['is_active']
    search_fields = ['label', 'user__email', 'bank_name', 'paypal_email', 'cashapp_cashtag', 'crypto_address']
    ordering = ['payment_method', 'label']
    fieldsets = (
        ('General', {
            'fields': ('user', 'payment_method', 'label', 'is_active'),
        }),
        ('Bank Transfer Details', {
            'fields': ('bank_name', 'account_name', 'account_number', 'routing_number', 'swift_code', 'iban', 'bank_address'),
            'classes': ('collapse',),
        }),
        ('PayPal Details', {
            'fields': ('paypal_email',),
            'classes': ('collapse',),
        }),
        ('Crypto Details', {
            'fields': ('crypto_currency', 'crypto_network', 'crypto_address'),
            'classes': ('collapse',),
        }),
        ('CashApp Details', {
            'fields': ('cashapp_cashtag', 'cashapp_name'),
            'classes': ('collapse',),
        }),
    )


