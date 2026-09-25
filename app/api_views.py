"""
Banking API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal

from app.models import (
    Account, Transaction, Beneficiary, Card, Loan,
    LoanRepayment, Notification, SupportTicket, ExchangeRate
)
from app.serializers import (
    AccountListSerializer, AccountDetailSerializer, AccountCreateSerializer,
    TransactionListSerializer, TransactionDetailSerializer,
    DepositSerializer, WithdrawalSerializer, TransferSerializer,
    BeneficiarySerializer, CardListSerializer, CardDetailSerializer,
    CardCreateSerializer, LoanListSerializer, LoanDetailSerializer,
    LoanApplicationSerializer, LoanRepaymentSerializer,
    NotificationSerializer, SupportTicketSerializer, ExchangeRateSerializer
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================
# ACCOUNT VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_list_view(request):
    """
    List all accounts for the authenticated user
    
    Query params:
        - status: Filter by account status (ACTIVE, PENDING, SUSPENDED, CLOSED)
        - account_type: Filter by account type (CHECKING, SAVINGS, etc.)
    """
    user = request.user
    accounts = Account.objects.filter(customer=user).select_related('customer')
    
    # Apply filters
    account_status = request.query_params.get('status')
    if account_status:
        accounts = accounts.filter(status=account_status.upper())
    
    account_type = request.query_params.get('account_type')
    if account_type:
        accounts = accounts.filter(account_type=account_type.upper())
    
    # Order by creation date
    accounts = accounts.order_by('-created_at')
    
    serializer = AccountListSerializer(accounts, many=True)
    
    return Response({
        'count': accounts.count(),
        'accounts': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_create_view(request):
    """
    Create a new bank account
    
    Request body:
        {
            "account_type": "CHECKING|SAVINGS|MONEY_MARKET|CD|PLATINUM|BUSINESS",
            "currency": "USD|NGN|EUR|GBP",
            "account_name": "My Savings Account" (optional),
            "is_joint_account": false
        }
    """
    serializer = AccountCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        account = serializer.save()
        detail_serializer = AccountDetailSerializer(account)
        
        return Response({
            'message': 'Account created successfully. Pending activation.',
            'account': detail_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_detail_view(request, account_number):
    """
    Get detailed information about a specific account
    """
    account = get_object_or_404(Account, account_number=account_number, customer=request.user)
    serializer = AccountDetailSerializer(account)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def account_update_view(request, account_number):
    """
    Update account settings
    
    Allowed updates:
        - account_name
        - daily_withdrawal_limit
        - daily_transfer_limit
    """
    account = get_object_or_404(Account, account_number=account_number, customer=request.user)
    
    # Only allow certain fields to be updated
    allowed_fields = ['account_name', 'daily_withdrawal_limit', 'daily_transfer_limit']
    
    for field in allowed_fields:
        if field in request.data:
            setattr(account, field, request.data[field])
    
    account.save()
    serializer = AccountDetailSerializer(account)
    
    return Response({
        'message': 'Account updated successfully',
        'account': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_statement_view(request, account_number):
    """
    Get account statement (transactions) for a specific period
    
    Query params:
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20)
    """
    account = get_object_or_404(Account, account_number=account_number, customer=request.user)
    
    # Get transactions for this account
    transactions = Transaction.objects.filter(account=account)
    
    # Apply date filters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        transactions = transactions.filter(initiated_at__gte=start_date)
    if end_date:
        transactions = transactions.filter(initiated_at__lte=end_date)
    
    # Order by date (newest first)
    transactions = transactions.order_by('-initiated_at')
    
    # Paginate
    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 20)
    paginated_transactions = paginator.paginate_queryset(transactions, request)
    
    serializer = TransactionListSerializer(paginated_transactions, many=True)
    
    return paginator.get_paginated_response({
        'account_number': account.account_number,
        'account_name': account.account_name,
        'current_balance': str(account.balance),
        'transactions': serializer.data
    })


# ============================================
# TRANSACTION VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_list_view(request):
    """
    List all transactions for the authenticated user
    
    Query params:
        - account_number: Filter by account
        - transaction_type: Filter by type (DEPOSIT, WITHDRAWAL, TRANSFER, etc.)
        - status: Filter by status (PENDING, COMPLETED, FAILED)
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
    """
    user = request.user
    transactions = Transaction.objects.filter(user=user).select_related('account')
    
    # Apply filters
    account_number = request.query_params.get('account_number')
    if account_number:
        transactions = transactions.filter(account__account_number=account_number)
    
    transaction_type = request.query_params.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type.upper())
    
    trans_status = request.query_params.get('status')
    if trans_status:
        transactions = transactions.filter(status=trans_status.upper())
    
    start_date = request.query_params.get('start_date')
    if start_date:
        transactions = transactions.filter(initiated_at__gte=start_date)
    
    end_date = request.query_params.get('end_date')
    if end_date:
        transactions = transactions.filter(initiated_at__lte=end_date)
    
    # Order by date (newest first)
    transactions = transactions.order_by('-initiated_at')
    
    # Paginate
    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 20)
    paginated_transactions = paginator.paginate_queryset(transactions, request)
    
    serializer = TransactionListSerializer(paginated_transactions, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_detail_view(request, transaction_id):
    """
    Get detailed information about a specific transaction
    """
    txn = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)
    serializer = TransactionDetailSerializer(txn)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def deposit_view(request):
    """
    Deposit money into an account
    
    Request body:
        {
            "account_number": "1234567890",
            "amount": 1000.00,
            "description": "Salary deposit" (optional),
            "reference_number": "REF123" (optional)
        }
    """
    serializer = DepositSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    data = serializer.validated_data
    
    # Get account
    try:
        account = Account.objects.select_for_update().get(
            account_number=data['account_number'],
            customer=user
        )
    except Account.DoesNotExist:
        return Response(
            {'error': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if account is active
    if account.status != 'ACTIVE':
        return Response(
            {'error': 'Account is not active or is frozen/closed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create transaction
    amount = data['amount']
    balance_before = account.balance
    balance_after = balance_before + amount
    
    txn = Transaction.objects.create(
        user=user,
        account=account,
        transaction_type='DEPOSIT',
        amount=amount,
        currency=account.currency,
        status='COMPLETED',
        channel='WEB',
        description=data.get('description', f'Deposit to {account.account_type} account'),
        reference_number=data.get('reference_number', ''),
        completed_at=timezone.now(),
        ip_address=get_client_ip(request)
    )
    
    # Update account balance
    account.balance = balance_after
    account.available_balance = balance_after - account.pending_balance
    account.save()
    
    serializer = TransactionDetailSerializer(txn)
    
    return Response({
        'message': 'Deposit successful',
        'transaction': serializer.data,
        'new_balance': str(account.balance)
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def withdrawal_view(request):
    """
    Withdraw money from an account
    
    Request body:
        {
            "account_number": "1234567890",
            "amount": 500.00,
            "description": "ATM withdrawal" (optional)
        }
    """
    serializer = WithdrawalSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    data = serializer.validated_data
    
    # Get account
    try:
        account = Account.objects.select_for_update().get(
            account_number=data['account_number'],
            customer=user
        )
    except Account.DoesNotExist:
        return Response(
            {'error': 'Account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if account is active
    if account.status != 'ACTIVE':
        return Response(
            {'error': 'Account is not active or is frozen/closed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user can make transfers
    if not user.can_make_transfers:
        return Response(
            {'error': 'You are not authorized to make withdrawals'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    amount = data['amount']
    
    # Check sufficient balance
    if account.available_balance < amount:
        return Response(
            {
                'error': 'Insufficient funds',
                'available_balance': str(account.available_balance),
                'requested_amount': str(amount)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check daily withdrawal limit
    if amount > account.daily_withdrawal_limit:
        return Response(
            {
                'error': f'Amount exceeds daily withdrawal limit of {user.currency_symbol}{account.daily_withdrawal_limit}',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check minimum balance
    new_balance = account.balance - amount
    if new_balance < account.minimum_balance:
        return Response(
            {
                'error': f'Withdrawal would bring balance below minimum of {user.currency_symbol}{account.minimum_balance}',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create transaction
    balance_before = account.balance
    balance_after = balance_before - amount
    
    txn = Transaction.objects.create(
        user=user,
        account=account,
        transaction_type='WITHDRAWAL',
        amount=amount,
        currency=account.currency,
        status='COMPLETED',
        channel='WEB',
        description=data.get('description', f'Withdrawal from {account.account_type} account'),
        completed_at=timezone.now(),
        ip_address=get_client_ip(request)
    )
    
    # Update account balance
    account.balance = balance_after
    account.available_balance = balance_after - account.pending_balance
    account.save()
    
    serializer = TransactionDetailSerializer(txn)
    
    return Response({
        'message': 'Withdrawal successful',
        'transaction': serializer.data,
        'new_balance': str(account.balance)
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def transfer_view(request):
    """
    Transfer money between accounts
    
    Request body:
        {
            "from_account_number": "1234567890",
            "beneficiary_account_number": "0987654321",
            "beneficiary_name": "John Doe",
            "beneficiary_bank": "ABC Bank",
            "amount": 1000.00,
            "description": "Payment for services" (optional),
            "save_beneficiary": false (optional),
            "beneficiary_nickname": "John" (required if save_beneficiary is true)
        }
    """
    serializer = TransferSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    data = serializer.validated_data
    
    # Check if user can make transfers
    if not user.can_make_transfers:
        return Response(
            {'error': 'You are not authorized to make transfers'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get from_account
    try:
        from_account = Account.objects.select_for_update().get(
            account_number=data['from_account_number'],
            customer=user
        )
    except Account.DoesNotExist:
        return Response(
            {'error': 'Source account not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if account is active
    if from_account.status != 'ACTIVE':
        return Response(
            {'error': 'Source account is not active or is frozen/closed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    amount = data['amount']
    
    # Check sufficient balance
    if from_account.available_balance < amount:
        return Response(
            {
                'error': 'Insufficient funds',
                'available_balance': str(from_account.available_balance),
                'requested_amount': str(amount)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check daily transfer limit
    if amount > from_account.daily_transfer_limit:
        return Response(
            {
                'error': f'Amount exceeds daily transfer limit of {user.currency_symbol}{from_account.daily_transfer_limit}',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check user's daily transfer limit
    if amount > user.daily_transfer_limit:
        return Response(
            {
                'error': f'Amount exceeds your daily transfer limit of {user.currency_symbol}{user.daily_transfer_limit}',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create transaction
    transfer_fee = Decimal('0.00')  # You can add fee calculation logic here
    balance_before = from_account.balance
    balance_after = balance_before - amount - transfer_fee
    
    txn = Transaction.objects.create(
        user=user,
        account=from_account,
        transaction_type='TRANSFER',
        amount=amount,
        currency=from_account.currency,
        fee=transfer_fee,
        status='COMPLETED',
        channel='WEB',
        beneficiary_account_number=data['beneficiary_account_number'],
        beneficiary_name=data['beneficiary_name'],
        beneficiary_bank=data['beneficiary_bank'],
        description=data.get('description', f'Transfer to {data["beneficiary_name"]}'),
        completed_at=timezone.now(),
        ip_address=get_client_ip(request)
    )
    
    # Update account balance
    from_account.balance = balance_after
    from_account.available_balance = balance_after - from_account.pending_balance
    from_account.save()
    
    # Save beneficiary if requested
    if data.get('save_beneficiary'):
        Beneficiary.objects.get_or_create(
            user=user,
            account_number=data['beneficiary_account_number'],
            bank_name=data['beneficiary_bank'],
            defaults={
                'nickname': data.get('beneficiary_nickname', data['beneficiary_name']),
                'account_name': data['beneficiary_name']
            }
        )
    
    serializer = TransactionDetailSerializer(txn)
    
    return Response({
        'message': 'Transfer successful',
        'transaction': serializer.data,
        'new_balance': str(from_account.balance)
    }, status=status.HTTP_201_CREATED)
"""
Banking API Views - Part 2
Beneficiary, Card, Loan, Notification, and Support views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone

from app.models import Beneficiary, Card, Loan, LoanRepayment, Notification, SupportTicket
from app.serializers import (
    BeneficiarySerializer, CardListSerializer, CardDetailSerializer,
    CardCreateSerializer, LoanListSerializer, LoanDetailSerializer,
    LoanApplicationSerializer, LoanRepaymentSerializer,
    NotificationSerializer, SupportTicketSerializer
)


# ============================================
# BENEFICIARY VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def beneficiary_list_view(request):
    """
    List all beneficiaries for the authenticated user
    
    Query params:
        - is_favorite: Filter by favorite status (true/false)
        - bank_name: Filter by bank name
    """
    user = request.user
    beneficiaries = Beneficiary.objects.filter(user=user)
    
    # Apply filters
    is_favorite = request.query_params.get('is_favorite')
    if is_favorite:
        is_fav_bool = is_favorite.lower() == 'true'
        beneficiaries = beneficiaries.filter(is_favorite=is_fav_bool)
    
    bank_name = request.query_params.get('bank_name')
    if bank_name:
        beneficiaries = beneficiaries.filter(bank_name__icontains=bank_name)
    
    # Order by favorites first, then by most recently used
    beneficiaries = beneficiaries.order_by('-is_favorite', '-last_used')
    
    serializer = BeneficiarySerializer(beneficiaries, many=True, context={'request': request})
    
    return Response({
        'count': beneficiaries.count(),
        'beneficiaries': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def beneficiary_create_view(request):
    """
    Add a new beneficiary
    
    Request body:
        {
            "nickname": "John Doe",
            "account_number": "0987654321",
            "account_name": "John Doe",
            "bank_name": "ABC Bank",
            "bank_code": "ABC" (optional),
            "routing_number": "123456789" (optional),
            "swift_code": "ABCBUS33" (optional)
        }
    """
    serializer = BeneficiarySerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        beneficiary = serializer.save()
        return Response({
            'message': 'Beneficiary added successfully',
            'beneficiary': BeneficiarySerializer(beneficiary, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def beneficiary_detail_view(request, beneficiary_id):
    """Get detailed information about a specific beneficiary"""
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id, user=request.user)
    serializer = BeneficiarySerializer(beneficiary, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def beneficiary_update_view(request, beneficiary_id):
    """
    Update beneficiary information
    
    Allowed updates:
        - nickname
        - account_name
        - is_favorite
    """
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id, user=request.user)
    
    serializer = BeneficiarySerializer(
        beneficiary,
        data=request.data,
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Beneficiary updated successfully',
            'beneficiary': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def beneficiary_delete_view(request, beneficiary_id):
    """Delete a beneficiary"""
    beneficiary = get_object_or_404(Beneficiary, id=beneficiary_id, user=request.user)
    beneficiary_name = beneficiary.nickname
    beneficiary.delete()
    
    return Response({
        'message': f'Beneficiary "{beneficiary_name}" deleted successfully'
    }, status=status.HTTP_200_OK)


# ============================================
# CARD VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_list_view(request):
    """
    List all cards for the authenticated user
    
    Query params:
        - status: Filter by status (ACTIVE, PENDING, BLOCKED, EXPIRED)
        - card_type: Filter by card type
        - is_virtual: Filter by virtual status (true/false)
    """
    user = request.user
    cards = Card.objects.filter(user=user).select_related('account')
    
    # Apply filters
    card_status = request.query_params.get('status')
    if card_status:
        cards = cards.filter(status=card_status.upper())
    
    card_type = request.query_params.get('card_type')
    if card_type:
        cards = cards.filter(card_type=card_type.upper())
    
    is_virtual = request.query_params.get('is_virtual')
    if is_virtual:
        is_virt_bool = is_virtual.lower() == 'true'
        cards = cards.filter(is_virtual=is_virt_bool)
    
    # Order by creation date (newest first)
    cards = cards.order_by('-created_at')
    
    serializer = CardListSerializer(cards, many=True)
    
    return Response({
        'count': cards.count(),
        'cards': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_create_view(request):
    """
    Apply for a new card
    
    Request body:
        {
            "card_type": "MASTERCARD_DEBIT|VISA_DEBIT|VERVE|MASTERCARD_CREDIT|VISA_CREDIT|GOLD|PLATINUM",
            "is_virtual": false,
            "account_number": "1234567890"
        }
    """
    serializer = CardCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        card = serializer.save()
        detail_serializer = CardDetailSerializer(card)
        
        return Response({
            'message': 'Card application submitted successfully. Pending approval.',
            'card': detail_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def card_detail_view(request, card_id):
    """Get detailed information about a specific card"""
    card = get_object_or_404(Card, id=card_id, user=request.user)
    serializer = CardDetailSerializer(card)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_block_view(request, card_id):
    """
    Block a card
    
    Request body:
        {
            "reason": "Lost card" (optional)
        }
    """
    card = get_object_or_404(Card, id=card_id, user=request.user)
    
    if card.status == 'BLOCKED':
        return Response({
            'error': 'Card is already blocked'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if card.status == 'CANCELLED':
        return Response({
            'error': 'Card is cancelled and cannot be blocked'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Block the card
    card.status = 'BLOCKED'
    card.blocked_at = timezone.now()
    card.blocked_reason = request.data.get('reason', 'Blocked by user')
    card.save()
    
    serializer = CardDetailSerializer(card)
    
    return Response({
        'message': 'Card blocked successfully',
        'card': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def card_unblock_view(request, card_id):
    """Unblock a card"""
    card = get_object_or_404(Card, id=card_id, user=request.user)
    
    if card.status != 'BLOCKED':
        return Response({
            'error': 'Card is not blocked'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Unblock the card
    card.status = 'ACTIVE'
    card.blocked_at = None
    card.blocked_reason = None
    card.save()
    
    serializer = CardDetailSerializer(card)
    
    return Response({
        'message': 'Card unblocked successfully',
        'card': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def card_update_limits_view(request, card_id):
    """
    Update card transaction limits
    
    Request body:
        {
            "daily_limit": 5000.00 (optional),
            "monthly_limit": 50000.00 (optional),
            "single_transaction_limit": 1000.00 (optional)
        }
    """
    card = get_object_or_404(Card, id=card_id, user=request.user)
    
    # Update limits
    if 'daily_limit' in request.data:
        card.daily_limit = request.data['daily_limit']
    
    if 'monthly_limit' in request.data:
        card.monthly_limit = request.data['monthly_limit']
    
    if 'single_transaction_limit' in request.data:
        card.single_transaction_limit = request.data['single_transaction_limit']
    
    card.save()
    serializer = CardDetailSerializer(card)
    
    return Response({
        'message': 'Card limits updated successfully',
        'card': serializer.data
    }, status=status.HTTP_200_OK)


# ============================================
# LOAN VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_list_view(request):
    """
    List all loans for the authenticated user
    
    Query params:
        - status: Filter by status (PENDING, APPROVED, ACTIVE, PAID, DEFAULTED, REJECTED)
        - loan_type: Filter by type (PERSONAL, MORTGAGE, AUTO, BUSINESS, EDUCATION)
    """
    user = request.user
    loans = Loan.objects.filter(customer=user).select_related('account')
    
    # Apply filters
    loan_status = request.query_params.get('status')
    if loan_status:
        loans = loans.filter(status=loan_status.upper())
    
    loan_type = request.query_params.get('loan_type')
    if loan_type:
        loans = loans.filter(loan_type=loan_type.upper())
    
    # Order by application date (newest first)
    loans = loans.order_by('-application_date')
    
    serializer = LoanListSerializer(loans, many=True)
    
    return Response({
        'count': loans.count(),
        'loans': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loan_apply_view(request):
    """
    Apply for a loan
    
    Request body:
        {
            "loan_type": "PERSONAL|MORTGAGE|AUTO|BUSINESS|EDUCATION",
            "principal_amount": 10000.00,
            "loan_term_months": 12,
            "collateral_description": "Car" (optional),
            "collateral_value": 15000.00 (optional),
            "account_number": "1234567890"
        }
    """
    serializer = LoanApplicationSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        loan = serializer.save()
        detail_serializer = LoanDetailSerializer(loan)
        
        return Response({
            'message': 'Loan application submitted successfully. Pending approval.',
            'loan': detail_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_detail_view(request, loan_number):
    """Get detailed information about a specific loan"""
    loan = get_object_or_404(Loan, loan_number=loan_number, customer=request.user)
    serializer = LoanDetailSerializer(loan)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_repayment_schedule_view(request, loan_number):
    """Get the repayment schedule for a loan"""
    loan = get_object_or_404(Loan, loan_number=loan_number, customer=request.user)
    
    # Get all repayments for this loan
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('payment_number')
    serializer = LoanRepaymentSerializer(repayments, many=True)
    
    return Response({
        'loan_number': loan.loan_number,
        'loan_type': loan.loan_type,
        'total_amount': str(loan.total_amount),
        'amount_paid': str(loan.amount_paid),
        'balance_remaining': str(loan.balance_remaining),
        'status': loan.status,
        'repayments': serializer.data
    }, status=status.HTTP_200_OK)


# ============================================
# NOTIFICATION VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list_view(request):
    """
    List all notifications for the authenticated user
    
    Query params:
        - is_read: Filter by read status (true/false)
        - notification_type: Filter by type (TRANSACTION, ACCOUNT, SECURITY, LOAN, CARD, SYSTEM, PROMOTIONAL)
        - priority: Filter by priority (LOW, MEDIUM, HIGH, URGENT)
    """
    user = request.user
    notifications = Notification.objects.filter(user=user)
    
    # Apply filters
    is_read = request.query_params.get('is_read')
    if is_read is not None:
        is_read_bool = is_read.lower() == 'true'
        notifications = notifications.filter(is_read=is_read_bool)
    
    notification_type = request.query_params.get('notification_type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type.upper())
    
    priority = request.query_params.get('priority')
    if priority:
        notifications = notifications.filter(priority=priority.upper())
    
    # Order by priority and creation date
    notifications = notifications.order_by('-priority', '-created_at')
    
    # Paginate
    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get('page_size', 20)
    paginated_notifications = paginator.paginate_queryset(notifications, request)
    
    serializer = NotificationSerializer(paginated_notifications, many=True)
    
    # Get unread count
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    return paginator.get_paginated_response({
        'unread_count': unread_count,
        'notifications': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_detail_view(request, notification_id):
    """
    Get detailed information about a specific notification
    Automatically marks it as read
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Mark as read if not already read
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    
    serializer = NotificationSerializer(notification)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_mark_read_view(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    
    return Response({
        'message': 'Notification marked as read'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_mark_all_read_view(request):
    """Mark all notifications as read"""
    user = request.user
    updated_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} notifications marked as read'
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def notification_delete_view(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    return Response({
        'message': 'Notification deleted successfully'
    }, status=status.HTTP_200_OK)


# ============================================
# SUPPORT TICKET VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def support_ticket_list_view(request):
    """
    List all support tickets for the authenticated user
    
    Query params:
        - status: Filter by status (OPEN, IN_PROGRESS, WAITING_CUSTOMER, RESOLVED, CLOSED)
        - category: Filter by category
    """
    user = request.user
    tickets = SupportTicket.objects.filter(user=user)
    
    # Apply filters
    ticket_status = request.query_params.get('status')
    if ticket_status:
        tickets = tickets.filter(status=ticket_status.upper())
    
    category = request.query_params.get('category')
    if category:
        tickets = tickets.filter(category=category.upper())
    
    # Order by priority and creation date
    tickets = tickets.order_by('-priority', '-created_at')
    
    serializer = SupportTicketSerializer(tickets, many=True)
    
    return Response({
        'count': tickets.count(),
        'tickets': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def support_ticket_create_view(request):
    """
    Create a new support ticket
    
    Request body:
        {
            "category": "ACCOUNT|TRANSACTION|CARD|LOAN|TECHNICAL|GENERAL|COMPLAINT",
            "priority": "LOW|MEDIUM|HIGH|URGENT",
            "subject": "Issue with my account",
            "description": "Detailed description of the issue"
        }
    """
    serializer = SupportTicketSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        ticket = serializer.save()
        return Response({
            'message': 'Support ticket created successfully',
            'ticket': SupportTicketSerializer(ticket).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def support_ticket_detail_view(request, ticket_number):
    """Get detailed information about a specific support ticket"""
    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number, user=request.user)
    serializer = SupportTicketSerializer(ticket)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# DASHBOARD/SUMMARY VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary_view(request):
    """
    Get a summary of user's banking data for dashboard
    """
    user = request.user
    
    # Get accounts summary
    accounts = Account.objects.filter(customer=user)
    total_balance = sum(acc.balance for acc in accounts if acc.status == 'ACTIVE')
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        user=user
    ).order_by('-initiated_at')[:5]
    
    # Get notifications
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()
    
    # Get active cards
    active_cards = Card.objects.filter(
        user=user,
        status='ACTIVE'
    ).count()
    
    # Get active loans
    active_loans = Loan.objects.filter(
        customer=user,
        status__in=['APPROVED', 'ACTIVE']
    )
    total_loan_balance = sum(loan.balance_remaining for loan in active_loans)
    
    return Response({
        'user': {
            'name': user.get_full_name,
            'email': user.email,
            'bank_id': user.bank_id,
            'customer_id': user.customer_id,
        },
        'accounts': {
            'total_count': accounts.count(),
            'active_count': accounts.filter(status='ACTIVE').count(),
            'total_balance': str(total_balance),
        },
        'transactions': {
            'recent': TransactionListSerializer(recent_transactions, many=True).data
        },
        'cards': {
            'active_count': active_cards
        },
        'loans': {
            'active_count': active_loans.count(),
            'total_balance': str(total_loan_balance)
        },
        'notifications': {
            'unread_count': unread_notifications
        }
    }, status=status.HTTP_200_OK)