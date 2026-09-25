"""
Serializers for the banking application
"""
from rest_framework import serializers
from app.models import (
    CustomUser, Account, Transaction, Beneficiary, 
    Card, Loan, LoanRepayment, Notification, 
    SupportTicket, AuditLog, ExchangeRate, TransactionLimit
)
from decimal import Decimal
from django.utils import timezone


# ============================================
# USER SERIALIZERS
# ============================================

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    total_balance = serializers.DecimalField(
        source='get_total_balance', 
        read_only=True,
        max_digits=15,
        decimal_places=2
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'middle_name', 'last_name', 'full_name',
            'phone_number', 'alternate_phone', 'bank_id', 'customer_id',
            'date_of_birth', 'gender', 'marital_status', 'number_of_dependents',
            'nationality', 'address', 'address_line2', 'city', 'state', 
            'country', 'postal_code', 'citizenship_status', 'preferred_currency',
            'preferred_language', 'account_status', 'total_balance',
            'can_apply_for_loans', 'can_apply_for_cards', 'can_make_transfers',
            'daily_transfer_limit', 'monthly_transfer_limit',
            'has_submitted_kyc', 'has_verified_kyc', 'email_verified',
            'phone_verified', 'two_factor_enabled', 'profile_image',
            'date_joined', 'last_activity'
        ]
        read_only_fields = [
            'id', 'email', 'bank_id', 'customer_id', 'full_name',
            'total_balance', 'has_verified_kyc', 'account_status',
            'date_joined', 'last_activity'
        ]


# ============================================
# ACCOUNT SERIALIZERS
# ============================================

class AccountListSerializer(serializers.ModelSerializer):
    """Serializer for listing accounts"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    masked_account_number = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'masked_account_number', 'account_name',
            'account_type', 'currency', 'balance', 'available_balance',
            'status', 'customer_name', 'bank_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'account_number', 'balance', 'available_balance']
    
    def get_masked_account_number(self, obj):
        """Mask account number for security"""
        if len(obj.account_number) > 4:
            return f"****{obj.account_number[-4:]}"
        return obj.account_number


class AccountDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single account"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    joint_holder_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'account_name', 'account_type', 'currency',
            'balance', 'available_balance', 'pending_balance',
            'ach_routing', 'swift_code', 'iban', 'bank_name', 'branch_name',
            'status',
            'daily_withdrawal_limit', 'daily_transfer_limit', 'minimum_balance',
            'overdraft_limit', 'interest_rate', 'last_interest_calculated',
            'is_joint_account', 'joint_holder_names', 'activation_fee',
            'activated_at', 'customer_name', 'customer_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'account_number', 'balance', 'available_balance',
            'pending_balance', 'ach_routing', 'swift_code', 'iban',
            'customer_name', 'customer_email'
        ]
    
    def get_joint_holder_names(self, obj):
        """Get names of joint account holders"""
        if obj.is_joint_account:
            return [holder.get_full_name for holder in obj.joint_holders.all()]
        return []


class AccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new accounts"""
    
    class Meta:
        model = Account
        fields = [
            'account_type', 'currency', 'account_name',
            'is_joint_account'
        ]
    
    def validate(self, data):
        """Validate account creation"""
        user = self.context['request'].user
        
        # Check if user has verified KYC
        if not user.has_verified_kyc:
            raise serializers.ValidationError(
                "You must complete KYC verification before opening an account."
            )
        
        return data
    
    def create(self, validated_data):
        """Create account with auto-generated fields"""
        user = self.context['request'].user
        validated_data['customer'] = user
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)


# ============================================
# TRANSACTION SERIALIZERS
# ============================================

class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer for listing transactions"""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 'currency',
            'fee', 'status', 'channel', 'beneficiary_name', 'beneficiary_account_number',
            'description', 'reference_number', 'account_number',
            'initiated_at', 'completed_at'
        ]
        read_only_fields = fields


class TransactionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single transaction"""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'user_email', 'account_number',
            'transaction_type', 'amount', 'currency', 'fee',
            'beneficiary_account_number', 'beneficiary_name', 'beneficiary_bank',
            'status', 'channel',
            'description', 'reference_number', 'external_reference',
            'initiated_at', 'completed_at', 'failed_at', 'failure_reason',
            'ip_address', 'receipt'
        ]
        read_only_fields = fields


class DepositSerializer(serializers.Serializer):
    """Serializer for deposit transactions"""
    account_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    reference_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_amount(self, value):
        """Validate deposit amount"""
        if value <= 0:
            raise serializers.ValidationError("Deposit amount must be greater than zero.")
        if value > 1000000:
            request = self.context.get('request')
            symbol = request.user.currency_symbol if request else '$'
            raise serializers.ValidationError(f"Deposit amount cannot exceed {symbol}1,000,000.")
        return value


class WithdrawalSerializer(serializers.Serializer):
    """Serializer for withdrawal transactions"""
    account_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_amount(self, value):
        """Validate withdrawal amount"""
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be greater than zero.")
        return value


class TransferSerializer(serializers.Serializer):
    """Serializer for transfer transactions"""
    from_account_number = serializers.CharField(max_length=20)
    beneficiary_account_number = serializers.CharField(max_length=20)
    beneficiary_name = serializers.CharField(max_length=200)
    beneficiary_bank = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    save_beneficiary = serializers.BooleanField(default=False)
    beneficiary_nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate transfer data"""
        # Check if from_account and to_account are different
        if data['from_account_number'] == data['beneficiary_account_number']:
            raise serializers.ValidationError(
                "Cannot transfer to the same account."
            )
        
        # Check amount
        if data['amount'] <= 0:
            raise serializers.ValidationError("Transfer amount must be greater than zero.")
        
        # If saving beneficiary, nickname is required
        if data.get('save_beneficiary') and not data.get('beneficiary_nickname'):
            raise serializers.ValidationError(
                "Beneficiary nickname is required when saving beneficiary."
            )
        
        return data


# ============================================
# BENEFICIARY SERIALIZERS
# ============================================

class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for beneficiaries"""
    masked_account_number = serializers.SerializerMethodField()
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'nickname', 'account_number', 'masked_account_number',
            'account_name', 'bank_name', 'bank_code', 'routing_number',
            'swift_code', 'is_verified', 'is_favorite',
            'created_at', 'last_used'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'last_used']
    
    def get_masked_account_number(self, obj):
        """Mask account number for security"""
        if len(obj.account_number) > 4:
            return f"****{obj.account_number[-4:]}"
        return obj.account_number
    
    def validate(self, data):
        """Validate beneficiary data"""
        user = self.context['request'].user
        
        # Check if beneficiary already exists
        if self.instance is None:  # Creating new beneficiary
            exists = Beneficiary.objects.filter(
                user=user,
                account_number=data['account_number'],
                bank_name=data['bank_name']
            ).exists()
            
            if exists:
                raise serializers.ValidationError(
                    "This beneficiary already exists."
                )
        
        return data
    
    def create(self, validated_data):
        """Create beneficiary"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


# ============================================
# CARD SERIALIZERS
# ============================================

class CardListSerializer(serializers.ModelSerializer):
    """Serializer for listing cards"""
    masked_card_number = serializers.SerializerMethodField()
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id', 'card_number', 'masked_card_number', 'card_type',
            'card_name', 'expiry_month', 'expiry_year', 'status',
            'is_virtual', 'daily_limit', 'account_number',
            'created_at', 'activated_at'
        ]
        read_only_fields = fields
    
    def get_masked_card_number(self, obj):
        """Mask card number for security"""
        if len(obj.card_number) >= 4:
            return f"**** **** **** {obj.card_number[-4:]}"
        return obj.card_number


class CardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single card"""
    masked_card_number = serializers.SerializerMethodField()
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id', 'card_number', 'masked_card_number', 'card_type', 'card_name',
            'cvv', 'expiry_month', 'expiry_year', 'is_expired',
            'daily_limit', 'monthly_limit', 'single_transaction_limit',
            'status', 'is_virtual', 'is_contactless_enabled',
            'is_online_enabled', 'is_international_enabled',
            'activation_fee', 'activated_at', 'account_number',
            'created_at', 'last_used', 'blocked_at', 'blocked_reason'
        ]
        read_only_fields = [
            'id', 'card_number', 'cvv', 'expiry_month', 'expiry_year',
            'is_expired', 'activation_fee', 'activated_at',
            'created_at', 'last_used', 'blocked_at'
        ]
    
    def get_masked_card_number(self, obj):
        """Mask card number for security"""
        if len(obj.card_number) >= 4:
            return f"**** **** **** {obj.card_number[-4:]}"
        return obj.card_number


class CardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new cards"""
    account_number = serializers.CharField(write_only=True)
    
    class Meta:
        model = Card
        fields = ['card_type', 'is_virtual', 'account_number']
    
    def validate(self, data):
        """Validate card creation"""
        user = self.context['request'].user
        
        # Check if user can apply for cards
        if not user.can_apply_for_cards:
            raise serializers.ValidationError(
                "You are not eligible to apply for cards at this time."
            )
        
        # Check if account exists and belongs to user
        account_number = data.get('account_number')
        try:
            account = Account.objects.get(
                account_number=account_number,
                customer=user,
                status='ACTIVE'
            )
            data['account'] = account
        except Account.DoesNotExist:
            raise serializers.ValidationError(
                "Account not found or not active."
            )
        
        return data
    
    def create(self, validated_data):
        """Create card"""
        user = self.context['request'].user
        account_number = validated_data.pop('account_number', None)
        validated_data['user'] = user
        validated_data['status'] = 'PENDING'
        
        return super().create(validated_data)


# ============================================
# LOAN SERIALIZERS
# ============================================

class LoanListSerializer(serializers.ModelSerializer):
    """Serializer for listing loans"""
    
    class Meta:
        model = Loan
        fields = [
            'id', 'loan_number', 'loan_type', 'principal_amount',
            'interest_rate', 'loan_term_months', 'total_amount',
            'amount_paid', 'balance_remaining', 'status',
            'application_date', 'maturity_date'
        ]
        read_only_fields = fields


class LoanDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single loan"""
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'id', 'loan_number', 'loan_type', 'principal_amount',
            'interest_rate', 'loan_term_months', 'monthly_payment',
            'total_interest', 'total_amount', 'amount_paid',
            'balance_remaining', 'application_date', 'approval_date',
            'disbursement_date', 'first_payment_date', 'maturity_date',
            'status', 'collateral_description', 'collateral_value',
            'account_number', 'customer_name'
        ]
        read_only_fields = fields


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for loan applications"""
    account_number = serializers.CharField(write_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'loan_type', 'principal_amount', 'loan_term_months',
            'collateral_description', 'collateral_value', 'account_number'
        ]
    
    def validate(self, data):
        """Validate loan application"""
        user = self.context['request'].user
        
        # Check if user can apply for loans
        if not user.can_apply_for_loans:
            raise serializers.ValidationError(
                "You are not eligible to apply for loans at this time."
            )
        
        # Check account
        account_number = data.get('account_number')
        try:
            account = Account.objects.get(
                account_number=account_number,
                customer=user,
                status='ACTIVE'
            )
            data['account'] = account
        except Account.DoesNotExist:
            raise serializers.ValidationError(
                "Account not found or not active."
            )
        
        # Validate loan amount
        symbol = user.currency_symbol
        if data['principal_amount'] < 1000:
            raise serializers.ValidationError(
                f"Minimum loan amount is {symbol}1,000."
            )

        if data['principal_amount'] > 1000000:
            raise serializers.ValidationError(
                f"Maximum loan amount is {symbol}1,000,000."
            )
        
        # Validate loan term
        if data['loan_term_months'] < 6:
            raise serializers.ValidationError(
                "Minimum loan term is 6 months."
            )
        
        if data['loan_term_months'] > 360:
            raise serializers.ValidationError(
                "Maximum loan term is 360 months (30 years)."
            )
        
        return data
    
    def create(self, validated_data):
        """Create loan application"""
        user = self.context['request'].user
        account_number = validated_data.pop('account_number', None)
        
        validated_data['customer'] = user
        validated_data['status'] = 'PENDING'
        
        # Calculate loan details
        principal = validated_data['principal_amount']
        rate = validated_data.get('interest_rate', Decimal('10.0'))
        months = validated_data['loan_term_months']
        
        # Simple interest calculation
        total_interest = (principal * rate * months) / (Decimal('100') * Decimal('12'))
        total_amount = principal + total_interest
        monthly_payment = total_amount / months
        
        validated_data['total_interest'] = total_interest
        validated_data['total_amount'] = total_amount
        validated_data['monthly_payment'] = monthly_payment
        validated_data['balance_remaining'] = total_amount
        
        return super().create(validated_data)


class LoanRepaymentSerializer(serializers.ModelSerializer):
    """Serializer for loan repayments"""
    loan_number = serializers.CharField(source='loan.loan_number', read_only=True)
    
    class Meta:
        model = LoanRepayment
        fields = [
            'id', 'loan_number', 'payment_number', 'due_date',
            'amount_due', 'amount_paid', 'paid_date',
            'is_paid', 'is_overdue', 'late_fee'
        ]
        read_only_fields = fields


# ============================================
# NOTIFICATION SERIALIZERS
# ============================================

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'priority', 'title', 'message',
            'action_url', 'is_read', 'read_at', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


# ============================================
# SUPPORT TICKET SERIALIZERS
# ============================================

class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'category', 'priority', 'subject',
            'description', 'status', 'user_email',
            'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'user_email', 'status', 'created_at']
    
    def create(self, validated_data):
        """Create support ticket"""
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['status'] = 'OPEN'
        return super().create(validated_data)


# ============================================
# EXCHANGE RATE SERIALIZERS
# ============================================

class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for exchange rates"""
    
    class Meta:
        model = ExchangeRate
        fields = [
            'id', 'from_currency', 'to_currency', 'rate',
            'effective_date', 'created_at'
        ]
        read_only_fields = fields