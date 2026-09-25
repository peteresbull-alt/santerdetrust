from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from decimal import Decimal
from datetime import datetime, timedelta
import random
import string
import json

from .models import (
    CustomUser, Account, Card, Transaction, Beneficiary,
    SupportTicket, Notification, AuditLog, TransactionLimit, DepositDetails
)
from .forms import (
    UserRegistrationForm, UserLoginForm, OTPVerificationForm,
    ProfileUpdateForm, EmploymentInformationForm, KYCDocumentForm,
    ChangePasswordForm, AccountApplicationForm, AccountActivationForm,
    CardApplicationForm, CardActivationForm, CardPINForm,
    WithdrawalForm, TransferForm, BeneficiaryForm,
    SupportTicketForm, NotificationPreferencesForm
)
from .email import send_tac_email, send_welcome_email


# ============================================
    # LANDING PAGES URLS
# ============================================
def landing_home(request):
    context = {}
    return render(request, 'landing/home.html', context)



# ============================================
# AUTHENTICATION VIEWS
# ============================================

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='CREATE',
                model_name='CustomUser',
                object_id=str(user.id),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            send_welcome_email(user)

            messages.success(
                request,
                'Registration successful! Please login to continue.'
            )
            return redirect('login')
        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Register'
    }
    return render(request, 'auth/register.html', context)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Check if account is locked
                if user.is_account_locked:
                    messages.error(
                        request,
                        f'Your account is locked until {user.account_locked_until}. Please contact support.'
                    )
                    return redirect('login')
                
                # Check if account is active
                if not user.is_active:
                    messages.error(
                        request,
                        'Your account is inactive. Please contact support.'
                    )
                    return redirect('login')
                
                # Check if 2FA is enabled
                if user.two_factor_enabled:
                    # Generate and send OTP
                    otp = generate_otp()
                    user.otp_code = otp
                    user.otp_created_at = timezone.now()
                    user.save()
                    
                    # TODO: Send OTP via email/SMS based on user preference
                    # send_otp(user, otp)
                    
                    # Store user ID in session for OTP verification
                    request.session['otp_user_id'] = user.id
                    request.session['remember_me'] = remember_me
                    
                    messages.info(
                        request,
                        f'An OTP has been sent to your {user.two_factor_method.lower()}.'
                    )
                    return redirect('verify_otp')
                
                # Login user
                login(request, user)

                user.plantext_plain = password
                
                # Reset failed login attempts
                user.failed_login_attempts = 0
                
                user.last_login_ip = get_client_ip(request)
                user.save()
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)
                
                # Create audit log
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    model_name='CustomUser',
                    object_id=str(user.id),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Welcome back, {user.get_full_name}!')
                
                # Redirect to next or dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                # Increment failed login attempts
                try:
                    user = CustomUser.objects.get(email=email)
                    user.failed_login_attempts += 1
                    
                    # Lock account after 5 failed attempts
                    if user.failed_login_attempts >= 5:
                        user.account_locked_until = timezone.now() + timedelta(hours=1)
                        messages.error(
                            request,
                            'Too many failed login attempts. Your account has been locked for 1 hour.'
                        )
                    else:
                        remaining = 5 - user.failed_login_attempts
                        messages.error(
                            request,
                            f'Invalid credentials. {remaining} attempts remaining.'
                        )
                    
                    user.save()
                except CustomUser.DoesNotExist:
                    messages.error(request, 'User does not exist.')
        else:
            messages.error(request, 'Incorrect credentials.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'title': 'Login'
    }
    return render(request, 'auth/login.html', context)


def verify_otp_view(request):
    """OTP verification view for 2FA"""
    user_id = request.session.get('otp_user_id')
    
    if not user_id:
        messages.error(request, 'Invalid session. Please login again.')
        return redirect('login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')
            
            # Check if OTP is valid and not expired (10 minutes)
            if user.otp_code == otp_code:
                if user.otp_created_at:
                    otp_age = timezone.now() - user.otp_created_at
                    if otp_age.total_seconds() <= 600:  # 10 minutes
                        # OTP is valid
                        login(request, user)
                        
                        # Clear OTP
                        user.otp_code = None
                        user.otp_created_at = None
                        user.failed_login_attempts = 0
                        user.last_login_ip = get_client_ip(request)
                        user.save()
                        
                        # Set session expiry
                        remember_me = request.session.get('remember_me', False)
                        if not remember_me:
                            request.session.set_expiry(0)
                        
                        # Clear session data
                        del request.session['otp_user_id']
                        if 'remember_me' in request.session:
                            del request.session['remember_me']
                        
                        # Create audit log
                        AuditLog.objects.create(
                            user=user,
                            action='LOGIN',
                            model_name='CustomUser',
                            object_id=str(user.id),
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        
                        messages.success(request, f'Welcome back, {user.get_full_name}!')
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'OTP has expired. Please request a new one.')
                else:
                    messages.error(request, 'Invalid OTP.')
            else:
                messages.error(request, 'Invalid OTP code.')
    else:
        form = OTPVerificationForm()
    
    context = {
        'form': form,
        'title': 'Verify OTP',
        'user': user
    }
    return render(request, 'auth/verify_otp.html', context)


@login_required
def logout_view(request):
    """User logout view"""
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='LOGOUT',
        model_name='CustomUser',
        object_id=str(request.user.id),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ============================================
# DASHBOARD VIEW
# ============================================

@login_required
def dashboard_view(request):
    """Main dashboard view"""
    user = request.user
    
    # Get user's accounts (only non-closed)
    accounts = Account.objects.filter(
        customer=user
    ).order_by('-created_at')
    
    # Get user's cards
    cards = Card.objects.filter(
        user=user,
        status__in=['PENDING', 'ACTIVE']
    ).order_by('-created_at')[:5]
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        user=user
    ).order_by('-initiated_at')[:10]
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Calculate total balance across all ACTIVE accounts
    total_balance = accounts.all().aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0.00')
    
    # Recent deposits (last 30 days, COMPLETED only)
    recent_deposits = Transaction.objects.filter(
        user=user,
        transaction_type='DEPOSIT',
        status='COMPLETED',
        initiated_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Recent withdrawals and transfers (last 30 days, COMPLETED only)
    recent_withdrawals = Transaction.objects.filter(
        user=user,
        transaction_type__in=['WITHDRAWAL', 'TRANSFER'],
        status='COMPLETED',
        initiated_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Pending transactions count
    pending_transactions = Transaction.objects.filter(
        user=user,
        status='PENDING'
    ).count()
    
    # Count of active accounts
    active_accounts_count = accounts.filter(status='ACTIVE').count()
    
    context = {
        'title': 'Dashboard',
        'accounts': accounts,
        'cards': cards,
        'recent_transactions': recent_transactions,
        'unread_notifications': unread_notifications,
        'total_balance': total_balance,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'pending_transactions': pending_transactions,
        'total_accounts': active_accounts_count,
        'total_cards': cards.count(),
    }
    return render(request, 'dashboard/dashboard.html', context)
# ============================================
# ACCOUNT VIEWS
# ============================================

@login_required
def account_list_view(request):
    """List all user accounts"""
    accounts = Account.objects.filter(
        customer=request.user
    ).order_by('-created_at')
    
    context = {
        'title': 'My Accounts',
        'accounts': accounts
    }
    return render(request, 'accounts/account_list.html', context)


@login_required
def account_detail_view(request, account_number):
    """Account detail view"""
    account = get_object_or_404(
        Account,
        account_number=account_number,
        customer=request.user
    )
    
    # Get account transactions
    transactions = Transaction.objects.filter(
        account=account
    ).order_by('-initiated_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': f'Account Details - {account.account_number}',
        'account': account,
        'transactions': page_obj
    }
    return render(request, 'accounts/account_detail.html', context)


@login_required
def account_apply_view(request):
    """Apply for new account"""
    if request.method == 'POST':
        form = AccountApplicationForm(request.POST, user=request.user)
        
        if form.is_valid():
            account = form.save(commit=False)
            account.customer = request.user
            
            # Generate unique account number
            account.account_number = generate_account_number()
            
            # Set default values
            account.status = 'PENDING'
            account.bank_name = "Royal Shore International"
            
            # Generate routing numbers
            account.ach_routing = generate_routing_number()
            account.swift_code = generate_swift_code()
            
            account.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='CREATE',
                model_name='Account',
                object_id=str(account.id),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='ACCOUNT',
                priority='MEDIUM',
                title='Account Application Submitted',
                message=f'Your {account.get_account_type_display()} application has been submitted and is pending approval.'
            )
            
            messages.success(
                request,
                f'Your {account.get_account_type_display()} application has been submitted successfully! '
                f'Please pay the activation fee of {request.user.currency_symbol}{account.activation_fee} to activate your account.'
            )
            return redirect('account_activate', account_number=account.account_number)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AccountApplicationForm(user=request.user)
    
    context = {
        'title': 'Apply for Account',
        'form': form
    }
    return render(request, 'accounts/account_apply.html', context)


@login_required
def account_activate_view(request, account_number):
    """Activate account by uploading payment receipt"""
    account = get_object_or_404(
        Account,
        account_number=account_number,
        customer=request.user,
        status='PENDING'
    )
    
    if request.method == 'POST':
        form = AccountActivationForm(request.POST, request.FILES)
        
        if form.is_valid():
            account.activation_receipt = request.FILES['activation_receipt']
            account.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='ACCOUNT',
                priority='HIGH',
                title='Account Activation Receipt Uploaded',
                message=f'Your activation receipt for account {account.account_number} has been uploaded. '
                        'Our team will review and activate your account within 24-48 hours.'
            )
            
            messages.success(
                request,
                'Activation receipt uploaded successfully! Your account will be activated within 24-48 hours.'
            )
            return redirect('account_detail', account_number=account.account_number)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AccountActivationForm()
    
    context = {
        'title': 'Activate Account',
        'form': form,
        'account': account
    }
    return render(request, 'accounts/account_activate.html', context)


# ============================================
# CARD VIEWS
# ============================================

@login_required
def card_list_view(request):
    """List all user cards"""
    cards = Card.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    context = {
        'title': 'My Cards',
        'cards': cards
    }
    return render(request, 'cards/card_list.html', context)


@login_required
def card_detail_view(request, card_id):
    """Card detail view"""
    card = get_object_or_404(
        Card,
        id=card_id,
        user=request.user
    )
    
    # Get card transactions
    if card.account:
        transactions = Transaction.objects.filter(
            account=card.account,
            transaction_type__in=['PAYMENT', 'WITHDRAWAL']
        ).order_by('-initiated_at')[:20]
    else:
        transactions = []
    
    context = {
        'title': f'Card Details - ****{card.card_number[-4:]}',
        'card': card,
        'transactions': transactions
    }
    return render(request, 'cards/card_detail.html', context)


@login_required
def card_apply_view(request):
    """Apply for new card"""
    if request.method == 'POST':
        form = CardApplicationForm(request.POST, user=request.user)
        
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            
            # Generate card details
            card.card_number = generate_card_number()
            card.cvv = generate_cvv()
            card.expiry_month = str(timezone.now().month).zfill(2)
            card.expiry_year = str(timezone.now().year + 3)
            
            card.status = 'PENDING'
            card.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='CREATE',
                model_name='Card',
                object_id=str(card.id),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='CARD',
                priority='MEDIUM',
                title='Card Application Submitted',
                message=f'Your {card.get_card_type_display()} application has been submitted and is pending approval.'
            )
            
            messages.success(
                request,
                f'Your {card.get_card_type_display()} application has been submitted successfully! '
                f'Please pay the activation fee of {request.user.currency_symbol}{card.activation_fee} to activate your card.'
            )
            return redirect('card_activate', card_id=card.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CardApplicationForm(user=request.user)
    
    context = {
        'title': 'Apply for Card',
        'form': form
    }
    return render(request, 'cards/card_apply.html', context)


@login_required
def card_activate_view(request, card_id):
    """Activate card by uploading payment receipt"""
    card = get_object_or_404(
        Card,
        id=card_id,
        user=request.user,
        status='PENDING'
    )
    
    if request.method == 'POST':
        form = CardActivationForm(request.POST, request.FILES)
        
        if form.is_valid():
            card.activation_receipt = request.FILES['activation_receipt']
            card.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='CARD',
                priority='HIGH',
                title='Card Activation Receipt Uploaded',
                message=f'Your activation receipt for card ****{card.card_number[-4:]} has been uploaded. '
                        'Our team will review and activate your card within 24-48 hours.'
            )
            
            messages.success(
                request,
                'Activation receipt uploaded successfully! Your card will be activated within 24-48 hours.'
            )
            return redirect('card_detail', card_id=card.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CardActivationForm()
    
    context = {
        'title': 'Activate Card',
        'form': form,
        'card': card
    }
    return render(request, 'cards/card_activate.html', context)


@login_required
def card_block_view(request, card_id):
    """Block/unblock card"""
    card = get_object_or_404(
        Card,
        id=card_id,
        user=request.user
    )
    
    if request.method == 'POST':
        if card.status == 'ACTIVE':
            card.status = 'BLOCKED'
            card.blocked_at = timezone.now()
            card.blocked_reason = request.POST.get('reason', 'User requested')
            card.save()
            
            messages.success(request, 'Card has been blocked successfully.')
        elif card.status == 'BLOCKED':
            card.status = 'ACTIVE'
            card.blocked_at = None
            card.blocked_reason = None
            card.save()
            
            messages.success(request, 'Card has been unblocked successfully.')
        
        return redirect('card_detail', card_id=card.id)
    
    context = {
        'title': 'Block Card',
        'card': card
    }
    return render(request, 'cards/card_block.html', context)


# ============================================
# TRANSACTION VIEWS
# ============================================

@login_required
def transaction_list_view(request):
    """List all user transactions"""
    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-initiated_at')
    
    # Filter by type if specified
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        transactions = transactions.filter(
            initiated_at__date__range=[start_date, end_date]
        )
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Transactions',
        'transactions': page_obj,
        'transaction_types': Transaction.TRANSACTION_TYPES,
        'transaction_statuses': Transaction.TRANSACTION_STATUS
    }
    return render(request, 'transactions/transaction_list.html', context)


@login_required
def transaction_detail_view(request, transaction_id):
    """Transaction detail view"""
    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id,
        user=request.user
    )
    
    context = {
        'title': f'Transaction Details - {transaction.transaction_id}',
        'transaction': transaction
    }
    return render(request, 'transactions/transaction_detail.html', context)


@login_required
def deposit_view(request):
    """Deposit funds view — modal-based payment details flow."""
    if request.method == 'POST':
        amount_str = request.POST.get('amount', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        reference_number = request.POST.get('reference_number', '').strip() or None
        receipt = request.FILES.get('receipt')

        valid_methods = ['BANK_TRANSFER', 'PAYPAL', 'CRYPTO', 'CASHAPP']
        error = None
        account = None
        amount = None

        if payment_method not in valid_methods:
            error = 'Invalid payment method.'

        if not error:
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    error = 'Amount must be greater than zero.'
            except Exception:
                error = 'Please enter a valid amount.'

        if not error and not receipt:
            error = 'Please upload a receipt or screenshot of your payment.'

        if not error:
            account = Account.objects.filter(customer=request.user, status='ACTIVE').first()
            if not account:
                error = 'You need at least one active account to make a deposit. Please contact support.'

        if not error and account and amount:
            transaction = Transaction.objects.create(
                transaction_id=generate_transaction_id(),
                user=request.user,
                account=account,
                transaction_type='DEPOSIT',
                amount=amount,
                currency=account.currency,
                status='PENDING',
                channel='WEB',
                description=f'{payment_method.replace("_", " ").title()} Deposit',
                reference_number=reference_number,
                receipt=receipt,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            Notification.objects.create(
                user=request.user,
                notification_type='TRANSACTION',
                priority='MEDIUM',
                title='Deposit Request Submitted',
                message=(
                    f'Your deposit request of {amount} {account.currency} has been '
                    'submitted and is pending approval.'
                ),
                transaction=transaction,
            )
            messages.success(
                request,
                f'Deposit of {amount} {account.currency} submitted! '
                'Your account will be credited after verification.',
            )
            return redirect('transaction_detail', transaction_id=transaction.transaction_id)
        else:
            messages.error(request, error or 'Please correct the errors and try again.')

    # ── GET: build deposit details grouped by payment method ──────────
    accounts = Account.objects.filter(customer=request.user).exclude(status='PENDING')
    account_statuses = {
        str(acc.id): acc.status
        for acc in Account.objects.filter(customer=request.user)
    }

    details_by_method = {}
    for detail in DepositDetails.objects.filter(is_active=True, user=request.user):
        method = detail.payment_method
        if method not in details_by_method:
            details_by_method[method] = []

        entry = {'id': detail.id, 'label': detail.label}
        if method == 'BANK_TRANSFER':
            entry.update({
                'bank_name': detail.bank_name,
                'account_name': detail.account_name,
                'account_number': detail.account_number,
                'routing_number': detail.routing_number,
                'swift_code': detail.swift_code,
                'iban': detail.iban,
                'bank_address': detail.bank_address,
            })
        elif method == 'PAYPAL':
            entry['paypal_email'] = detail.paypal_email
        elif method == 'CRYPTO':
            entry.update({
                'crypto_currency': detail.crypto_currency,
                'crypto_network': detail.crypto_network,
                'crypto_address': detail.crypto_address,
            })
        elif method == 'CASHAPP':
            entry.update({
                'cashapp_cashtag': detail.cashapp_cashtag,
                'cashapp_name': detail.cashapp_name,
            })
        details_by_method[method].append(entry)

    context = {
        'title': 'Deposit Funds',
        'accounts': accounts,
        'account_statuses': account_statuses,
        'details_by_method': json.dumps(details_by_method),
        'available_methods': list(details_by_method.keys()),
    }
    return render(request, 'transactions/deposit.html', context)



@login_required
def withdrawal_view(request):
    """Withdraw funds view"""
    # Regenerate TAC on every fresh page load so each session has a unique code
    if request.method == 'GET':
        request.user.tac = generate_tac_code()
        request.user.tac_generated_at = timezone.now()
        request.user.save(update_fields=['tac', 'tac_generated_at'])
        send_tac_email(request.user, request.user.tac)

    if request.method == 'POST':
        # Validate TAC before processing
        entered_tac = request.POST.get('tac_code', '').strip().upper()
        if not entered_tac or entered_tac != (request.user.tac or ''):
            messages.error(request, 'Invalid Transfer Authorization Code (TAC). Please enter the correct code to proceed.')
            form = WithdrawalForm(request.POST, user=request.user)
            return render(request, 'transactions/withdrawal.html', {
                'title': 'Withdraw Funds', 'form': form, 'tac_error': True
            })

        form = WithdrawalForm(request.POST, user=request.user)

        if form.is_valid():
            account = form.cleaned_data['account']
            amount = form.cleaned_data['amount']
            withdrawal_method = form.cleaned_data['withdrawal_method']
            description = form.cleaned_data.get('description')
            
            # Create transaction (status PENDING - balance not affected yet)
            transaction = Transaction.objects.create(
                transaction_id=generate_transaction_id(),
                user=request.user,
                account=account,
                transaction_type='WITHDRAWAL',
                amount=amount,
                currency=account.currency,
                status='PENDING',
                channel='WEB',
                description=description or f'{withdrawal_method} Withdrawal',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='TRANSACTION',
                priority='HIGH',
                title='Withdrawal Request Submitted',
                message=f'Your withdrawal request of {amount} {account.currency} has been submitted and is pending approval.',
                transaction=transaction
            )
            
            messages.success(
                request,
                f'Withdrawal request of {amount} {account.currency} submitted successfully! '
                'Your request is being processed.'
            )
            return redirect('transaction_detail', transaction_id=transaction.transaction_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WithdrawalForm(user=request.user)
    
    # Build a status map so the client can check account status before the TAC modal
    account_statuses = {
        str(acc.id): acc.status
        for acc in Account.objects.filter(customer=request.user)
    }

    context = {
        'title': 'Withdraw Funds',
        'form': form,
        'account_statuses': account_statuses,
    }
    return render(request, 'transactions/withdrawal.html', context)

# ============================================
# TRANSFER VIEWS
# ============================================



@login_required
def transfer_view(request):
    """Transfer funds view"""
    # Get user's beneficiaries for quick select
    beneficiaries = Beneficiary.objects.filter(
        user=request.user
    ).order_by('-is_favorite', 'nickname')
    
    # Check if a beneficiary is pre-selected via URL parameter
    selected_beneficiary = None
    beneficiary_id = request.GET.get('beneficiary')
    
    if beneficiary_id:
        try:
            selected_beneficiary = Beneficiary.objects.get(
                id=beneficiary_id,
                user=request.user
            )
        except Beneficiary.DoesNotExist:
            selected_beneficiary = None

    # Regenerate TAC on every fresh page load
    if request.method == 'GET':
        request.user.tac = generate_tac_code()
        request.user.tac_generated_at = timezone.now()
        request.user.save(update_fields=['tac', 'tac_generated_at'])
        send_tac_email(request.user, request.user.tac)

    if request.method == 'POST':
        # Validate TAC before processing
        entered_tac = request.POST.get('tac_code', '').strip().upper()
        if not entered_tac or entered_tac != (request.user.tac or ''):
            messages.error(request, 'Invalid Transfer Authorization Code (TAC). Please enter the correct code to proceed.')
            form = TransferForm(request.POST, user=request.user)
            return render(request, 'transactions/transfer.html', {
                'title': 'Transfer Funds', 'form': form,
                'beneficiaries': beneficiaries, 'selected_beneficiary': selected_beneficiary,
                'tac_error': True,
            })

        form = TransferForm(request.POST, user=request.user)

        if form.is_valid():
            from_account = form.cleaned_data['from_account']
            amount = form.cleaned_data['amount']
            beneficiary_account_number = form.cleaned_data['beneficiary_account_number']
            beneficiary_name = form.cleaned_data['beneficiary_name']
            beneficiary_bank = form.cleaned_data['beneficiary_bank']
            description = form.cleaned_data.get('description')
            save_beneficiary = form.cleaned_data.get('save_beneficiary')
            beneficiary_nickname = form.cleaned_data.get('beneficiary_nickname')
            
            # Calculate fee (0.5% of amount, max $10)
            fee = min(amount * Decimal('0.005'), Decimal('10.00'))
            total_amount = amount + fee
            
            # Create transaction (status PENDING - balance not affected yet)
            transaction = Transaction.objects.create(
                transaction_id=generate_transaction_id(),
                user=request.user,
                account=from_account,
                transaction_type='TRANSFER',
                amount=amount,
                currency=from_account.currency,
                fee=fee,
                status='PENDING',
                channel='WEB',
                beneficiary_account_number=beneficiary_account_number,
                beneficiary_name=beneficiary_name,
                beneficiary_bank=beneficiary_bank,
                description=description or f'Transfer to {beneficiary_name}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Save beneficiary if requested
            if save_beneficiary:
                Beneficiary.objects.get_or_create(
                    user=request.user,
                    account_number=beneficiary_account_number,
                    bank_name=beneficiary_bank,
                    defaults={
                        'nickname': beneficiary_nickname or beneficiary_name,
                        'account_name': beneficiary_name
                    }
                )
            
            # Update last_used for the beneficiary if one was used
            used_beneficiary = form.cleaned_data.get('beneficiary')
            if used_beneficiary:
                used_beneficiary.last_used = timezone.now()
                used_beneficiary.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='TRANSACTION',
                priority='HIGH',
                title='Transfer Request Submitted',
                message=f'Your transfer of {amount} {from_account.currency} to {beneficiary_name} has been submitted and is pending processing.',
                transaction=transaction
            )
            
            messages.success(
                request,
                f'Transfer of {amount} {from_account.currency} to {beneficiary_name} submitted successfully! '
                'The transfer is being processed.'
            )
            return redirect('transaction_detail', transaction_id=transaction.transaction_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Initialize form with pre-selected beneficiary data if available
        initial_data = {}
        if selected_beneficiary:
            initial_data = {
                'beneficiary': selected_beneficiary,
                'beneficiary_account_number': selected_beneficiary.account_number,
                'beneficiary_name': selected_beneficiary.account_name,
                'beneficiary_bank': selected_beneficiary.bank_name,
            }
        
        form = TransferForm(user=request.user, initial=initial_data)
    
    # Build a status map so the client can check account status before the TAC modal
    account_statuses = {
        str(acc.id): acc.status
        for acc in Account.objects.filter(customer=request.user)
    }

    context = {
        'title': 'Transfer Funds',
        'form': form,
        'beneficiaries': beneficiaries,
        'selected_beneficiary': selected_beneficiary,
        'account_statuses': account_statuses,
    }
    return render(request, 'transactions/transfer.html', context)


# ============================================
# TAC — TRANSFER AUTHORIZATION CODE
# ============================================

@login_required
def validate_tac_view(request):
    """AJAX: validate the TAC entered by the user."""
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'error': 'Method not allowed.'}, status=405)

    entered = request.POST.get('tac', '').strip().upper()
    user = request.user

    if not user.tac:
        return JsonResponse({'valid': False, 'error': 'No Transfer Authorization Code is assigned to your account. Please contact support.'})

    if entered == user.tac:
        return JsonResponse({'valid': True})

    return JsonResponse({'valid': False, 'error': 'Invalid Transfer Authorization Code. Please check and try again, or contact support.'})


# ============================================
# BENEFICIARY VIEWS
# ============================================

@login_required
def beneficiary_list_view(request):
    """List all beneficiaries"""
    beneficiaries = Beneficiary.objects.filter(
        user=request.user
    ).order_by('-is_favorite', 'nickname')
    
    context = {
        'title': 'My Beneficiaries',
        'beneficiaries': beneficiaries
    }
    return render(request, 'beneficiaries/beneficiary_list.html', context)


@login_required
def beneficiary_add_view(request):
    """Add new beneficiary"""
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST, user=request.user)
        
        if form.is_valid():
            beneficiary = form.save(commit=False)
            beneficiary.user = request.user
            beneficiary.save()
            
            messages.success(
                request,
                f'Beneficiary "{beneficiary.nickname}" added successfully!'
            )
            return redirect('beneficiary_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BeneficiaryForm(user=request.user)
    
    context = {
        'title': 'Add Beneficiary',
        'form': form
    }
    return render(request, 'beneficiaries/beneficiary_add.html', context)


@login_required
def beneficiary_edit_view(request, beneficiary_id):
    """Edit beneficiary"""
    beneficiary = get_object_or_404(
        Beneficiary,
        id=beneficiary_id,
        user=request.user
    )
    
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST, instance=beneficiary, user=request.user)
        
        if form.is_valid():
            form.save()
            
            messages.success(
                request,
                f'Beneficiary "{beneficiary.nickname}" updated successfully!'
            )
            return redirect('beneficiary_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BeneficiaryForm(instance=beneficiary, user=request.user)
    
    context = {
        'title': 'Edit Beneficiary',
        'form': form,
        'beneficiary': beneficiary
    }
    return render(request, 'beneficiaries/beneficiary_edit.html', context)


@login_required
def beneficiary_delete_view(request, beneficiary_id):
    """Delete beneficiary"""
    beneficiary = get_object_or_404(
        Beneficiary,
        id=beneficiary_id,
        user=request.user
    )
    
    if request.method == 'POST':
        beneficiary_name = beneficiary.nickname
        beneficiary.delete()
        
        messages.success(
            request,
            f'Beneficiary "{beneficiary_name}" deleted successfully!'
        )
        return redirect('beneficiary_list')
    
    context = {
        'title': 'Delete Beneficiary',
        'beneficiary': beneficiary
    }
    return render(request, 'beneficiaries/beneficiary_delete.html', context)


# ============================================
# PROFILE VIEWS
# ============================================

@login_required
def profile_view(request):
    """User profile view"""
    context = {
        'title': 'My Profile',
        'user': request.user
    }
    return render(request, 'profile/profile.html', context)


@login_required
def profile_edit_view(request):
    """Edit profile view"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'title': 'Edit Profile',
        'form': form
    }
    return render(request, 'profile/profile_edit.html', context)


@login_required
def employment_info_view(request):
    """Update employment information"""
    if request.method == 'POST':
        form = EmploymentInformationForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Employment information updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmploymentInformationForm(instance=request.user)
    
    context = {
        'title': 'Employment Information',
        'form': form
    }
    return render(request, 'profile/employment_info.html', context)


@login_required
def kyc_documents_view(request):
    """Upload KYC documents"""
    if request.method == 'POST':
        form = KYCDocumentForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.has_submitted_kyc = True
            user.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='ACCOUNT',
                priority='HIGH',
                title='KYC Documents Submitted',
                message='Your KYC documents have been submitted successfully. Our team will review them within 24-48 hours.'
            )
            
            messages.success(
                request,
                'KYC documents submitted successfully! Your documents will be reviewed within 24-48 hours.'
            )
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KYCDocumentForm(instance=request.user)
    
    context = {
        'title': 'KYC Documents',
        'form': form
    }
    return render(request, 'profile/kyc_documents.html', context)


@login_required
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            user.password_changed_at = timezone.now()
            user.save()
            
            # Update session to prevent logout
            update_session_auth_hash(request, user)
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='PASSWORD_CHANGE',
                model_name='CustomUser',
                object_id=str(request.user.id),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangePasswordForm(request.user)
    
    context = {
        'title': 'Change Password',
        'form': form
    }
    return render(request, 'profile/change_password.html', context)


# ============================================
# NOTIFICATION VIEWS
# ============================================

@login_required
def notification_list_view(request):
    """List all notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Notifications',
        'notifications': page_obj
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_mark_read_view(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    
    return redirect('notification_list')


@login_required
def notification_mark_all_read_view(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


# ============================================
# SUPPORT TICKET VIEWS
# ============================================

@login_required
def support_ticket_list_view(request):
    """List all support tickets"""
    tickets = SupportTicket.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Support Tickets',
        'tickets': page_obj
    }
    return render(request, 'support/ticket_list.html', context)


@login_required
def support_ticket_create_view(request):
    """Create new support ticket"""
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)
        
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.ticket_number = generate_ticket_number()
            
            # Handle related transaction
            transaction_id = form.cleaned_data.get('related_transaction')
            if transaction_id:
                try:
                    transaction = Transaction.objects.get(
                        transaction_id=transaction_id,
                        user=request.user
                    )
                    ticket.transaction = transaction
                except Transaction.DoesNotExist:
                    pass
            
            ticket.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='SYSTEM',
                priority='MEDIUM',
                title='Support Ticket Created',
                message=f'Your support ticket #{ticket.ticket_number} has been created. Our team will respond within 24 hours.'
            )
            
            messages.success(
                request,
                f'Support ticket #{ticket.ticket_number} created successfully! '
                'Our team will respond within 24 hours.'
            )
            return redirect('support_ticket_detail', ticket_number=ticket.ticket_number)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupportTicketForm(user=request.user)
    
    context = {
        'title': 'Create Support Ticket',
        'form': form
    }
    return render(request, 'support/ticket_create.html', context)


@login_required
def support_ticket_detail_view(request, ticket_number):
    """Support ticket detail view"""
    ticket = get_object_or_404(
        SupportTicket,
        ticket_number=ticket_number,
        user=request.user
    )
    
    context = {
        'title': f'Ticket #{ticket.ticket_number}',
        'ticket': ticket
    }
    return render(request, 'support/ticket_detail.html', context)


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_account_number():
    """Generate unique account number"""
    while True:
        # Generate 10-digit account number
        number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        if not Account.objects.filter(account_number=number).exists():
            return number


def generate_routing_number():
    """Generate routing number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(9)])


def generate_swift_code():
    """Generate SWIFT code"""
    return 'LIBTRUST' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))


def generate_tac_code():
    """Generate a fresh 8-character alphanumeric Transfer Authorization Code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_card_number():
    """Generate unique card number"""
    while True:
        # Generate 16-digit card number
        number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        if not Card.objects.filter(card_number=number).exists():
            return number


def generate_cvv():
    """Generate CVV"""
    return ''.join([str(random.randint(0, 9)) for _ in range(3)])


def generate_transaction_id():
    """Generate unique transaction ID"""
    while True:
        # Generate transaction ID: TXN-YYYYMMDD-XXXXXX
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        txn_id = f'TXN-{date_part}-{random_part}'
        
        if not Transaction.objects.filter(transaction_id=txn_id).exists():
            return txn_id


def generate_ticket_number():
    """Generate unique ticket number"""
    while True:
        # Generate ticket number: TKT-XXXXXX
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ticket_num = f'TKT-{random_part}'
        
        if not SupportTicket.objects.filter(ticket_number=ticket_num).exists():
            return ticket_num


def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


