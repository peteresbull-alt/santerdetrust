"""
Signal handlers for the banking application
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_login_failed, user_logged_in
from django.db.models import F
from django.utils import timezone
from decimal import Decimal
import random
import string
from datetime import datetime, timedelta


def generate_unique_id(model_class, field_name, prefix, length):
    """
    Generate a unique ID for a model
    """
    while True:
        random_id = ''.join(random.choices(string.digits, k=length))
        unique_id = f"{prefix}{random_id}" if prefix else random_id
        
        if not model_class.objects.filter(**{field_name: unique_id}).exists():
            return unique_id


@receiver(post_save, sender='app.CustomUser')
def generate_user_identifiers(sender, instance, created, **kwargs):
    """
    Generate unique identifiers for user after creation
    """
    if created:
        updated = False
        
        # Generate bank_id if not exists
        if not instance.bank_id:
            instance.bank_id = generate_unique_id(sender, 'bank_id', '', 10)
            updated = True
        
        # Generate customer_id if not exists
        if not instance.customer_id:
            timestamp = datetime.now().strftime("%Y%m%d")
            random_suffix = ''.join(random.choices(string.digits, k=6))
            instance.customer_id = f"CUST{timestamp}{random_suffix}"
            
            # Ensure uniqueness
            while sender.objects.filter(customer_id=instance.customer_id).exists():
                random_suffix = ''.join(random.choices(string.digits, k=6))
                instance.customer_id = f"CUST{timestamp}{random_suffix}"
            updated = True
        
        # Generate referral_code if not exists
        if not instance.referral_code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            while sender.objects.filter(referral_code=code).exists():
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            instance.referral_code = code
            updated = True
        
        # Save if any updates were made
        if updated:
            # Use update instead of save to avoid triggering signal again
            sender.objects.filter(pk=instance.pk).update(
                bank_id=instance.bank_id,
                customer_id=instance.customer_id,
                referral_code=instance.referral_code
            )


@receiver(post_save, sender='app.Account')
def generate_account_identifiers(sender, instance, created, **kwargs):
    """
    Generate unique identifiers for account after creation
    """
    if created:
        updated = False
        
        # Generate account number if not exists
        if not instance.account_number:
            instance.account_number = generate_unique_id(sender, 'account_number', '', 12)
            updated = True
        
        # Generate ACH routing if not exists
        if not instance.ach_routing:
            instance.ach_routing = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            updated = True
        
        # Generate SWIFT code if not exists (for international accounts)
        if not instance.swift_code:
            instance.swift_code = f"OPTIUS33XXX"  # Your bank's SWIFT code
            updated = True
        
        # Set account name if not provided
        if not instance.account_name:
            instance.account_name = f"{instance.customer.get_full_name} - {instance.account_type}"
            updated = True
        
        # Save if any updates were made
        if updated:
            sender.objects.filter(pk=instance.pk).update(
                account_number=instance.account_number,
                ach_routing=instance.ach_routing,
                swift_code=instance.swift_code,
                account_name=instance.account_name
            )


@receiver(post_save, sender='app.Transaction')
def generate_transaction_id(sender, instance, created, **kwargs):
    """
    Generate unique transaction ID after creation
    """
    if created and not instance.transaction_id:
        # Format: TXN + YYYYMMDD + HHMMSS + 6 random digits
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.digits, k=6))
        transaction_id = f"TXN{timestamp}{random_suffix}"
        
        # Ensure uniqueness
        while sender.objects.filter(transaction_id=transaction_id).exists():
            random_suffix = ''.join(random.choices(string.digits, k=6))
            transaction_id = f"TXN{timestamp}{random_suffix}"
        
        sender.objects.filter(pk=instance.pk).update(transaction_id=transaction_id)


@receiver(pre_save, sender='app.Transaction')
def remember_previous_transaction_status(sender, instance, **kwargs):
    """
    Remember the status stored in the DB so post_save can tell whether
    this save is the one that moves the transaction to COMPLETED.
    """
    instance._previous_status = (
        sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
        if instance.pk else None
    )

    # Stamp the completion time when the transaction is marked COMPLETED (e.g. from admin)
    if instance.status == 'COMPLETED' and not instance.completed_at:
        instance.completed_at = timezone.now()


@receiver(post_save, sender='app.Transaction')
def update_account_balance(sender, instance, **kwargs):
    """
    Credit/debit the account when a transaction is completed
    """
    # Only process the save that transitions the transaction to COMPLETED,
    # so re-saving (e.g. editing in admin) never re-applies it
    if instance.status != 'COMPLETED' or not instance.account_id:
        return
    if getattr(instance, '_previous_status', None) == 'COMPLETED':
        return

    # Calculate balance change based on transaction type
    if instance.transaction_type in ['DEPOSIT', 'INTEREST', 'REFUND', 'LOAN_DISBURSEMENT']:
        change = instance.amount
    elif instance.transaction_type in ['WITHDRAWAL', 'TRANSFER', 'PAYMENT', 'FEE', 'LOAN_REPAYMENT']:
        change = -(instance.amount + (instance.fee or 0))
    else:
        return

    # Apply the change in the DB (F expression) so a stale in-memory account can't clobber it
    from app.models import Account  # Import here to avoid circular import
    Account.objects.filter(pk=instance.account_id).update(
        balance=F('balance') + change,
        updated_at=timezone.now(),
    )


@receiver(post_save, sender='app.Transaction')
def create_transaction_notification(sender, instance, created, **kwargs):
    """
    Create notification for completed transactions
    """
    if instance.status == 'COMPLETED':
        from app.models import Notification  # Import here to avoid circular import
        
        # Check if notification already exists for this transaction
        if not Notification.objects.filter(transaction=instance).exists():
            # Determine notification title and message based on transaction type
            if instance.transaction_type == 'DEPOSIT':
                title = "Deposit Successful"
                message = f"Your account has been credited with {instance.currency} {instance.amount}."
            elif instance.transaction_type == 'WITHDRAWAL':
                title = "Withdrawal Successful"
                message = f"You have withdrawn {instance.currency} {instance.amount} from your account."
            elif instance.transaction_type == 'TRANSFER':
                title = "Transfer Successful"
                message = f"You have transferred {instance.currency} {instance.amount} to {instance.beneficiary_name}."
            else:
                title = f"{instance.transaction_type.title()} Successful"
                message = f"Your {instance.transaction_type.lower()} of {instance.currency} {instance.amount} was successful."
            
            Notification.objects.create(
                user=instance.user,
                notification_type='TRANSACTION',
                priority='MEDIUM',
                title=title,
                message=message,
                transaction=instance
            )


@receiver(post_save, sender='app.Card')
def generate_card_details(sender, instance, created, **kwargs):
    """
    Generate card number, CVV, and expiry date after creation
    """
    if created:
        updated = False
        
        # Generate card number based on card type
        if not instance.card_number:
            if 'MASTERCARD' in instance.card_type.upper():
                prefix = "5555"
            elif 'VISA' in instance.card_type.upper():
                prefix = "4111"
            elif 'VERVE' in instance.card_type.upper():
                prefix = "5061"
            else:
                prefix = "0000"
            
            # Generate rest of card number
            rest = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            card_number = prefix + rest
            
            # Ensure uniqueness
            while sender.objects.filter(card_number=card_number).exists():
                rest = ''.join([str(random.randint(0, 9)) for _ in range(12)])
                card_number = prefix + rest
            
            instance.card_number = card_number
            updated = True
        
        # Generate CVV
        if not instance.cvv:
            instance.cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
            updated = True
        
        # Generate expiry date (4 years from now)
        if not instance.expiry_month or not instance.expiry_year:
            expiry_date = datetime.now() + timedelta(days=4*365)
            instance.expiry_month = expiry_date.strftime("%m")
            instance.expiry_year = expiry_date.strftime("%Y")
            updated = True
        
        # Set card name if not provided
        if not instance.card_name:
            instance.card_name = instance.user.get_full_name
            updated = True
        
        # Save if any updates were made
        if updated:
            sender.objects.filter(pk=instance.pk).update(
                card_number=instance.card_number,
                cvv=instance.cvv,
                expiry_month=instance.expiry_month,
                expiry_year=instance.expiry_year,
                card_name=instance.card_name
            )


@receiver(post_save, sender='app.Loan')
def generate_loan_number(sender, instance, created, **kwargs):
    """
    Generate unique loan number after creation
    """
    if created and not instance.loan_number:
        # Format: LOAN + YYYYMMDD + 6 random digits
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.digits, k=6))
        loan_number = f"LOAN{timestamp}{random_suffix}"
        
        # Ensure uniqueness
        while sender.objects.filter(loan_number=loan_number).exists():
            random_suffix = ''.join(random.choices(string.digits, k=6))
            loan_number = f"LOAN{timestamp}{random_suffix}"
        
        sender.objects.filter(pk=instance.pk).update(loan_number=loan_number)


@receiver(post_save, sender='app.SupportTicket')
def generate_ticket_number(sender, instance, created, **kwargs):
    """
    Generate unique ticket number after creation
    """
    if created and not instance.ticket_number:
        # Format: TICK + YYYYMMDD + 6 random digits
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.digits, k=6))
        ticket_number = f"TICK{timestamp}{random_suffix}"
        
        # Ensure uniqueness
        while sender.objects.filter(ticket_number=ticket_number).exists():
            random_suffix = ''.join(random.choices(string.digits, k=6))
            ticket_number = f"TICK{timestamp}{random_suffix}"
        
        sender.objects.filter(pk=instance.pk).update(ticket_number=ticket_number)


@receiver(post_save, sender='app.CustomUser')
def log_user_action(sender, instance, created, **kwargs):
    """
    Log user creation in audit log
    """
    if created:
        from app.models import AuditLog  # Import here to avoid circular import
        
        AuditLog.objects.create(
            user=instance,
            action='CREATE',
            model_name='CustomUser',
            object_id=str(instance.id),
            changes={
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
            }
        )

# ============================================
# Login & password audit trail
# ============================================

def _stack():
    """Current call stack as (posix-style path, function name) pairs"""
    import traceback
    return [(f.filename.replace(chr(92), '/'), f.name) for f in traceback.extract_stack()]


def _password_change_source():
    """Best guess at what changed a password, from the current call stack"""
    frames = _stack()
    files = ' '.join(path for path, _ in frames)
    names = {name for _, name in frames}
    if 'management/commands/changepassword' in files:
        return 'manage.py changepassword'
    if 'management/commands/createsuperuser' in files:
        return 'manage.py createsuperuser'
    if 'change_password_view' in names:
        return 'profile: change password page'
    if any(name == 'password_change' and path.endswith('contrib/admin/sites.py') for path, name in frames):
        return 'admin: "Change password" link (top right)'
    if 'user_change_password' in names:
        return "admin: user's change-password form"
    if any(name == 'form_valid' and path.endswith('contrib/auth/views.py') for path, name in frames):
        return 'forgot password: emailed reset link'
    if 'contrib/admin' in files or 'contrib/auth/admin' in files:
        return 'admin site'
    app_frames = [(path, name) for path, name in frames if '/app/' in path and not path.endswith('signals.py')]
    if app_frames:
        path, name = app_frames[-1]
        return f"{path.rsplit('/', 1)[-1]}:{name}"
    return 'unknown'


def _is_password_rehash():
    """True when Django is only re-hashing a correct password on login (password itself unchanged)"""
    return any(name == 'setter' and 'contrib/auth' in path for path, name in _stack())


@receiver(pre_save, sender='app.CustomUser')
def remember_password_change(sender, instance, **kwargs):
    """Flag saves that change the stored password so post_save can record them"""
    instance._password_changed = False
    update_fields = kwargs.get('update_fields')
    if not instance.pk or (update_fields is not None and 'password' not in update_fields):
        return
    old = sender.objects.filter(pk=instance.pk).values_list('password', flat=True).first()
    if old is not None and old != instance.password and not _is_password_rehash():
        instance._password_changed = True
        instance._password_change_source = _password_change_source()
        instance.password_changed_at = timezone.now()


@receiver(post_save, sender='app.CustomUser')
def log_password_change(sender, instance, created, **kwargs):
    """Record every password change in the audit log (never the password itself)"""
    if created or not getattr(instance, '_password_changed', False):
        return
    instance._password_changed = False
    if instance._password_change_source == 'profile: change password page':
        return  # change_password_view logs this itself, with IP and browser
    from app.models import AuditLog  # Import here to avoid circular import
    AuditLog.objects.create(
        user=instance,
        action='PASSWORD_CHANGE',
        model_name='CustomUser',
        object_id=str(instance.id),
        changes={'via': getattr(instance, '_password_change_source', 'unknown')},
    )
    instance._password_changed = False


def _client_ip(request):
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or None


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request=None, **kwargs):
    """Record why a login failed, so 'wrong password' vs 'unknown email' is visible later"""
    from app.models import AuditLog, CustomUser  # Import here to avoid circular import
    email = (credentials.get('username') or credentials.get('email') or '').strip()
    user = CustomUser.objects.filter(email__iexact=email).first() if email else None
    if user is None:
        reason = 'no account with this email'
    elif not user.is_active:
        reason = 'account is inactive'
    else:
        reason = 'wrong password'
    AuditLog.objects.create(
        user=user,
        action='LOGIN_FAILED',
        model_name='CustomUser',
        object_id=str(user.id) if user else '',
        changes={'email_entered': email[:254], 'reason': reason, 'page': request.path if request else ''},
        ip_address=_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT', '')[:255] if request else ''),
    )


@receiver(user_logged_in)
def log_admin_login(sender, request, user, **kwargs):
    """Record successful admin-site logins (the site's own /login/ view already logs its logins)"""
    if not request or not request.path.startswith('/admin/login/'):
        return
    from app.models import AuditLog  # Import here to avoid circular import
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        model_name='CustomUser',
        object_id=str(user.id),
        changes={'page': request.path},
        ip_address=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
    )
