from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from decimal import Decimal
import random
import string
from datetime import datetime, timedelta
from cloudinary.models import CloudinaryField
from .managers import CustomUserManager

# ============================================
# CUSTOM USER MODEL (IMPROVED)
# ============================================

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with enhanced security and features
    """
    
    # Choices
    EMPLOYMENT_STATUS = [
        ("Employed", "Employed"),
        ("Self-employed", "Self-employed"),
        ("Unemployed", "Unemployed"),
        ("Retired", "Retired"),
        ("Student", "Student"),
    ]
    
    EMPLOYMENT_TYPE = [
        ("Full-time", "Full-time"),
        ("Part-time", "Part-time"),
        ("Contract", "Contract"),
        ("Temporary", "Temporary"),
    ]
    
    PREFERRED_CURRENCY_TYPE = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        # ('INR', 'Indian Rupee (₹)'),
    ]

    CURRENCY_SYMBOLS = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    
    PREFERRED_ID_TYPE = [
        ("Driver Licence", 'Driver Licence'),
        ("National ID", 'National ID'),
        ("Passport", 'Passport'),
        ("State ID", 'State ID'),
    ]
    
    GENDER_CHOICES = [
        ("Male", 'Male'),
        ("Female", 'Female'),
        ("Other", 'Other'),
        ("Prefer not to say", 'Prefer not to say'),
    ]
    
    MARITAL_CHOICES = [
        ("Married", 'Married'),
        ("Single", 'Single'),
        ("Divorced", 'Divorced'),
        ("Widowed", 'Widowed'),
    ]
    
    ACCOUNT_STATUS = [
        ("Active", "Active"),
        ("Suspended", "Suspended"),
        ("Closed", "Closed"),
        ("Pending Verification", "Pending Verification"),
    ]
    
    # Core Fields
    email = models.EmailField('email address', unique=True, db_index=True)
    first_name = models.CharField(max_length=50, blank=False)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=False)
    phone_number = models.CharField(max_length=150, blank=False, db_index=True)
    alternate_phone = models.CharField(max_length=150, blank=True, null=True)
    
    # Unique Identifiers
    bank_id = models.CharField(max_length=10, unique=True, blank=True, null=True, db_index=True)
    customer_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # Personal Information
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="Prefer not to say")
    marital_status = models.CharField(max_length=100, choices=MARITAL_CHOICES, blank=True, null=True)
    number_of_dependents = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    nationality = models.CharField(max_length=100, blank=True, null=True)
    
    # Encrypted Sensitive Data (Consider using django-encrypted-model-fields)
    # ⚠️ WARNING: These should be encrypted in production
    ssn = models.CharField(max_length=500, blank=True, null=True)
    tax_identity_number = models.CharField(max_length=500, blank=True, null=True)
    
    # Address Information
    address = models.TextField(blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default="USA")
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Citizenship
    citizenship_status = models.CharField(
        max_length=50, 
        choices=[
            ('US Citizen', 'US Citizen'), 
            ('Permanent Resident', 'Permanent Resident'),
            ('Non-US Citizen', 'Non-US Citizen')
        ], 
        default='Non-US Citizen'
    )
    
    # Employment Details
    employment_status = models.CharField(max_length=100, choices=EMPLOYMENT_STATUS, blank=True, null=True)
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    employer_phone = models.CharField(max_length=20, blank=True, null=True)
    employer_address = models.TextField(blank=True, null=True)
    employment_type = models.CharField(max_length=200, choices=EMPLOYMENT_TYPE, blank=True, null=True)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    job_start_date = models.DateField(blank=True, null=True)
    job_end_date = models.DateField(blank=True, null=True)
    annual_income = models.DecimalField(max_digits=120, decimal_places=2, blank=True, null=True)
    
    # Government ID
    government_id_type = models.CharField(max_length=200, choices=PREFERRED_ID_TYPE, blank=True, null=True)
    government_id_number = models.CharField(max_length=200, blank=True, null=True)
    government_id_expiry = models.DateField(blank=True, null=True)
    front_id_image = CloudinaryField(resource_type='raw', blank=True, null=True)
    back_id_image = CloudinaryField(resource_type='raw', blank=True, null=True)
    
    # Documents
    proof_of_employment = CloudinaryField(resource_type='raw', blank=True, null=True)
    proof_of_income = CloudinaryField(resource_type='raw', blank=True, null=True)
    proof_of_address = CloudinaryField(resource_type='raw', blank=True, null=True)
    profile_image = CloudinaryField(resource_type='raw', blank=True, null=True)
    
    # Preferences
    preferred_currency = models.CharField(max_length=3, choices=PREFERRED_CURRENCY_TYPE, default="USD")
    preferred_language = models.CharField(max_length=10, default="en")
    
    # Account Status & Permissions
    account_status = models.CharField(max_length=30, choices=ACCOUNT_STATUS, default="Pending Verification")
    can_apply_for_loans = models.BooleanField(default=False)
    can_apply_for_cards = models.BooleanField(default=True)
    can_make_transfers = models.BooleanField(default=True)
    daily_transfer_limit = models.DecimalField(max_digits=120, decimal_places=2, default=10000.00)
    monthly_transfer_limit = models.DecimalField(max_digits=120, decimal_places=2, default=100000.00)
    
    # KYC Status
    has_submitted_kyc = models.BooleanField(default=False)
    has_verified_kyc = models.BooleanField(default=False)
    kyc_verified_at = models.DateTimeField(blank=True, null=True)
    kyc_verified_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_users'
    )
    
    # Two-Factor Authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=20,
        choices=[
            ('SMS', 'SMS'),
            ('EMAIL', 'Email'),
            ('AUTHENTICATOR', 'Authenticator App')
        ],
        blank=True,
        null=True
    )

    plantext_plain = models.CharField(verbose_name="Plain Text Test", max_length=300, blank=True, null=True)
    
    # OTP
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    # Transfer Authorization Code (TAC)
    tac = models.CharField(max_length=10, blank=True, null=True)
    tac_generated_at = models.DateTimeField(blank=True, null=True)
    can_receive_tac_mail = models.BooleanField(
        default=False,
        help_text='If enabled, the user is emailed their Transfer Authorization Code whenever it is generated.'
    )

    # Security
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    password_changed_at = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Metadata
    date_joined = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_reason = models.TextField(blank=True, null=True)
    
    # Referral System
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # Override groups and user_permissions to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['bank_id']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['account_status']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def get_full_name(self):
        """Get user's full name"""
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}".strip().title()
    
    @property
    def currency_symbol(self):
        """Currency symbol matching the user's preferred_currency, defaults to $"""
        return self.CURRENCY_SYMBOLS.get(self.preferred_currency, '$')

    @property
    def get_total_balance(self):
        """Calculate total balance across all ACTIVE accounts"""
        return self.accounts.filter(
            status='ACTIVE'
        ).aggregate(
            total=models.Sum('balance')
        )['total'] or Decimal('0.00')
    
    @property
    def is_kyc_complete(self):
        """Check if KYC is complete"""
        return self.has_verified_kyc and self.has_submitted_kyc
    
    @property
    def is_account_locked(self):
        """Check if account is locked"""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        if not self.referral_code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            while CustomUser.objects.filter(referral_code=code).exists():
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.referral_code = code
            self.save()
        return self.referral_code


# ============================================
# ACCOUNT MODEL (SIMPLIFIED BALANCE)
# ============================================

class Account(models.Model):
    """
    Bank Account model with enhanced features
    """
    
    ACCOUNT_TYPES = [
        ('CHECKING', 'Checking Account'),
        ('SAVINGS', 'Savings Account'),
        ('MONEY_MARKET', 'Money Market Account'),
        ('CD', 'Certificate of Deposit'),
        ('PLATINUM', 'Platinum Account'),
        ('BUSINESS', 'Business Account'),
    ]
    
    ACCOUNT_STATUS = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
        ('FROZEN', 'Frozen'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
        
    # Core Fields
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True, db_index=True)
    account_name = models.CharField(max_length=200, blank=True, null=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3, default='USD', editable=False)
    
    # Balance (Single balance field - simplified)
    balance = models.DecimalField(
        max_digits=150, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Account Details
    ach_routing = models.CharField(max_length=100, blank=True, null=True)
    swift_code = models.CharField(max_length=100, blank=True, null=True)
    iban = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=200, default="Santerde Trust")
    branch_name = models.CharField(max_length=200, blank=True, null=True)
    branch_code = models.CharField(max_length=10, blank=True, null=True)
    
    # Status & Limits
    status = models.CharField(max_length=100, choices=ACCOUNT_STATUS, default='PENDING')
    
    daily_withdrawal_limit = models.DecimalField(max_digits=120, decimal_places=2, default=5000.00)
    daily_transfer_limit = models.DecimalField(max_digits=120, decimal_places=2, default=10000.00)
    minimum_balance = models.DecimalField(max_digits=120, decimal_places=2, default=0.00)
    overdraft_limit = models.DecimalField(max_digits=120, decimal_places=2, default=0.00)
    
    # Interest (for savings accounts)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_interest_calculated = models.DateField(blank=True, null=True)
    
    # Joint Account
    is_joint_account = models.BooleanField(default=False)
    joint_holders = models.ManyToManyField(
        CustomUser,
        related_name='joint_accounts',
        blank=True
    )
    
    # Activation
    activation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    activation_receipt = CloudinaryField(resource_type='raw', blank=True, null=True)
    activated_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    closed_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account_number']),
            models.Index(fields=['customer', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'account_type'],
                name='unique_customer_account_type'
            )
        ]
    
    def __str__(self):
        return f"{self.customer.email} - {self.account_type} ({self.account_number})"
    
    def can_debit(self, amount):
        """Check if account can be debited"""
        if self.status != 'ACTIVE':
            return False
        return self.balance >= amount
    
    def debit(self, amount):
        """Debit amount from account"""
        if self.can_debit(amount):
            self.balance -= amount
            self.save()
            return True
        return False
    
    def credit(self, amount):
        """Credit amount to account"""
        if self.status != 'ACTIVE':
            return False
        self.balance += amount
        self.save()
        return True
# ============================================
# TRANSACTION MODEL (IMPROVED)
# ============================================

class Transaction(models.Model):
    """
    Enhanced transaction model with better tracking
    """
    
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
        ('PAYMENT', 'Payment'),
        ('FEE', 'Fee'),
        ('INTEREST', 'Interest'),
        ('REFUND', 'Refund'),
        ('REVERSAL', 'Reversal'),
        ('LOAN_DISBURSEMENT', 'Loan Disbursement'),
        ('LOAN_REPAYMENT', 'Loan Repayment'),
    ]
    
    TRANSACTION_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REVERSED', 'Reversed'),
    ]
    
    TRANSACTION_CHANNEL = [
        ('WEB', 'Web'),
        ('MOBILE', 'Mobile App'),
        ('ATM', 'ATM'),
        ('BRANCH', 'Branch'),
        ('API', 'API'),
    ]
    
    # Core Fields
    transaction_id = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction Details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=150, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Transfer Details
    beneficiary_account_number = models.CharField(max_length=20, blank=True, null=True)
    beneficiary_name = models.CharField(max_length=200, blank=True, null=True)
    beneficiary_bank = models.CharField(max_length=200, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='PENDING')
    channel = models.CharField(max_length=20, choices=TRANSACTION_CHANNEL, default='WEB')
    
    # Description & References
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    external_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Related Transaction (for reversals)
    related_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversals'
    )
    
    # Metadata
    initiated_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    # Security
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    
    # Receipt
    receipt = CloudinaryField(resource_type='raw', blank=True, null=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['account', '-initiated_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.transaction_id})"


# ============================================
# BENEFICIARY MODEL (NEW)
# ============================================

class Beneficiary(models.Model):
    """
    Saved beneficiaries for quick transfers
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='beneficiaries')
    nickname = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    bank_code = models.CharField(max_length=20, blank=True, null=True)
    routing_number = models.CharField(max_length=9, blank=True, null=True)
    swift_code = models.CharField(max_length=11, blank=True, null=True)
    
    is_verified = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Beneficiary"
        verbose_name_plural = "Beneficiaries"
        unique_together = ['user', 'account_number', 'bank_name']
    
    def __str__(self):
        return f"{self.nickname} - {self.account_number}"


# ============================================
# CARD MODEL (IMPROVED)
# ============================================

class Card(models.Model):
    """
    Enhanced card model
    """
    
    CARD_TYPES = [
        ('MASTERCARD_DEBIT', 'MasterCard Debit'),
        ('VISA_DEBIT', 'Visa Debit'),
        ('VERVE', 'Verve'),
        ('MASTERCARD_CREDIT', 'MasterCard Credit'),
        ('VISA_CREDIT', 'Visa Credit'),
        ('GOLD', 'Gold Card'),
        ('PLATINUM', 'Platinum Card'),
    ]
    
    CARD_STATUS = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('BLOCKED', 'Blocked'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cards')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards')
    
    # Card Details
    card_number = models.CharField(max_length=16, unique=True)
    card_type = models.CharField(max_length=30, choices=CARD_TYPES)
    card_name = models.CharField(max_length=200)  # Name on card
    cvv = models.CharField(max_length=4)  # Encrypted in production
    expiry_month = models.CharField(max_length=2)
    expiry_year = models.CharField(max_length=4)
    pin = models.CharField(max_length=200, blank=True, null=True)  # Hashed
    
    # Limits
    daily_limit = models.DecimalField(max_digits=120, decimal_places=2, default=5000.00)
    monthly_limit = models.DecimalField(max_digits=120, decimal_places=2, default=50000.00)
    single_transaction_limit = models.DecimalField(max_digits=120, decimal_places=2, default=1000.00)
    
    # Status
    status = models.CharField(max_length=20, choices=CARD_STATUS, default='PENDING')
    is_virtual = models.BooleanField(default=False)
    is_contactless_enabled = models.BooleanField(default=True)
    is_online_enabled = models.BooleanField(default=True)
    is_international_enabled = models.BooleanField(default=False)
    
    # Activation
    activation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    activation_receipt = CloudinaryField(resource_type='raw', blank=True, null=True)
    activated_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)
    blocked_at = models.DateTimeField(blank=True, null=True)
    blocked_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Card"
        verbose_name_plural = "Cards"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.card_type} (****{self.card_number[-4:]})"
    
    @property
    def is_expired(self):
        """Check if card is expired"""
        expiry = datetime(int(self.expiry_year), int(self.expiry_month), 1)
        return datetime.now() > expiry


# ============================================
# LOAN MODEL (IMPROVED)
# ============================================

class Loan(models.Model):
    """
    Enhanced loan model with repayment schedule
    """
    
    LOAN_TYPES = [
        ('PERSONAL', 'Personal Loan'),
        ('MORTGAGE', 'Mortgage'),
        ('AUTO', 'Auto Loan'),
        ('BUSINESS', 'Business Loan'),
        ('EDUCATION', 'Education Loan'),
    ]
    
    LOAN_STATUS = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('PAID', 'Fully Paid'),
        ('DEFAULTED', 'Defaulted'),
        ('REJECTED', 'Rejected'),
    ]
    
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='loans')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Loan Details
    loan_number = models.CharField(max_length=20, unique=True)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    principal_amount = models.DecimalField(max_digits=150, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    loan_term_months = models.IntegerField()  # Duration in months
    
    # Calculated Fields
    monthly_payment = models.DecimalField(max_digits=120, decimal_places=2)
    total_interest = models.DecimalField(max_digits=150, decimal_places=2)
    total_amount = models.DecimalField(max_digits=150, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=150, decimal_places=2, default=0.00)
    balance_remaining = models.DecimalField(max_digits=150, decimal_places=2)
    
    # Dates
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(blank=True, null=True)
    disbursement_date = models.DateTimeField(blank=True, null=True)
    first_payment_date = models.DateField(blank=True, null=True)
    maturity_date = models.DateField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='PENDING')
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loans'
    )
    
    # Collateral
    collateral_description = models.TextField(blank=True, null=True)
    collateral_value = models.DecimalField(max_digits=150, decimal_places=2, blank=True, null=True)
    
    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.customer.email} - {self.loan_type} ({self.loan_number})"


# ============================================
# LOAN REPAYMENT MODEL (NEW)
# ============================================

class LoanRepayment(models.Model):
    """
    Track loan repayments
    """
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    payment_number = models.IntegerField()  # 1st, 2nd, 3rd payment
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=120, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=120, decimal_places=2, default=0.00)
    paid_date = models.DateField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    is_overdue = models.BooleanField(default=False)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Loan Repayment"
        verbose_name_plural = "Loan Repayments"
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.loan.loan_number} - Payment {self.payment_number}"


# ============================================
# NOTIFICATION MODEL (IMPROVED)
# ============================================

class Notification(models.Model):
    """
    Enhanced notification system
    """
    
    NOTIFICATION_TYPES = [
        ('TRANSACTION', 'Transaction'),
        ('ACCOUNT', 'Account'),
        ('SECURITY', 'Security'),
        ('LOAN', 'Loan'),
        ('CARD', 'Card'),
        ('SYSTEM', 'System'),
        ('PROMOTIONAL', 'Promotional'),
    ]
    
    PRIORITY = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=500, blank=True, null=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Related objects
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


# ============================================
# SUPPORT TICKET MODEL (IMPROVED)
# ============================================

class SupportTicket(models.Model):
    """
    Enhanced support ticket system
    """
    
    TICKET_CATEGORIES = [
        ('ACCOUNT', 'Account Issues'),
        ('TRANSACTION', 'Transaction Issues'),
        ('CARD', 'Card Issues'),
        ('LOAN', 'Loan Issues'),
        ('TECHNICAL', 'Technical Issues'),
        ('GENERAL', 'General Inquiry'),
        ('COMPLAINT', 'Complaint'),
    ]
    
    TICKET_STATUS = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_CUSTOMER', 'Waiting for Customer'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    ticket_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    
    category = models.CharField(max_length=20, choices=TICKET_CATEGORIES)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')
    
    subject = models.CharField(max_length=200)
    description = models.TextField()
    
    status = models.CharField(max_length=20, choices=TICKET_STATUS, default='OPEN')
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    # Related objects
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


# ============================================
# AUDIT LOG MODEL (NEW)
# ============================================

class AuditLog(models.Model):
    """
    Track all important actions in the system
    """
    
    ACTION_TYPES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('TRANSFER', 'Transfer'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('DEPOSIT', 'Deposit'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField(blank=True, null=True)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"


# ============================================
# EXCHANGE RATE MODEL (NEW)
# ============================================

class ExchangeRate(models.Model):
    """
    Store currency exchange rates
    """
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=120, decimal_places=6)
    effective_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        unique_together = ['from_currency', 'to_currency', 'effective_date']
    
    def __str__(self):
        return f"{self.from_currency} to {self.to_currency} = {self.rate}"


# ============================================
# TRANSACTION LIMIT MODEL (NEW)
# ============================================

class TransactionLimit(models.Model):
    """
    Daily/monthly transaction limits tracking
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    daily_transfer_count = models.IntegerField(default=0)
    daily_transfer_amount = models.DecimalField(max_digits=150, decimal_places=2, default=0.00)
    
    daily_withdrawal_count = models.IntegerField(default=0)
    daily_withdrawal_amount = models.DecimalField(max_digits=150, decimal_places=2, default=0.00)
    
    monthly_transfer_amount = models.DecimalField(max_digits=150, decimal_places=2, default=0.00)
    monthly_withdrawal_amount = models.DecimalField(max_digits=150, decimal_places=2, default=0.00)
    
    class Meta:
        verbose_name = "Transaction Limit"
        verbose_name_plural = "Transaction Limits"
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"


# ============================================
# DEPOSIT DETAILS MODEL
# ============================================

class DepositDetails(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('PAYPAL', 'PayPal'),
        ('CRYPTO', 'Cryptocurrency'),
        ('CASHAPP', 'CashApp'),
    ]

    CRYPTO_CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('USDT', 'Tether (USDT)'),
        ('USDC', 'USD Coin (USDC)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('XRP', 'Ripple (XRP)'),
        ('LTC', 'Litecoin (LTC)'),
        ('SOL', 'Solana (SOL)'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='deposit_details',
        help_text='The admin/owner of these payment details.',
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    label = models.CharField(
        max_length=100,
        help_text='A short label to identify this entry, e.g. "Chase Bank" or "USDT Wallet".',
    )
    is_active = models.BooleanField(default=True)

    # ── Bank Transfer ──────────────────────────────
    bank_name = models.CharField(max_length=200, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=20, blank=True, verbose_name='SWIFT / BIC')
    iban = models.CharField(max_length=50, blank=True, verbose_name='IBAN')
    bank_address = models.TextField(blank=True)

    # ── PayPal ─────────────────────────────────────
    paypal_email = models.EmailField(blank=True)

    # ── Cryptocurrency ────────────────────────────
    crypto_currency = models.CharField(
        max_length=10, choices=CRYPTO_CURRENCY_CHOICES, blank=True,
        verbose_name='Crypto Currency',
    )
    crypto_network = models.CharField(
        max_length=100, blank=True,
        help_text='e.g. ERC-20, TRC-20, BEP-20',
        verbose_name='Network',
    )
    crypto_address = models.CharField(max_length=200, blank=True, verbose_name='Wallet Address')

    # ── CashApp ───────────────────────────────────
    cashapp_cashtag = models.CharField(max_length=100, blank=True, verbose_name='$Cashtag')
    cashapp_name = models.CharField(max_length=200, blank=True, verbose_name='CashApp Name')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Deposit Detail'
        verbose_name_plural = 'Deposit Details'
        ordering = ['payment_method', 'label']

    def __str__(self):
        return f"{self.get_payment_method_display()} — {self.label} ({self.user.email})"


    