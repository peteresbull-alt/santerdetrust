from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import (
    CustomUser, Account, Card, Transaction, Beneficiary, 
    SupportTicket, Notification
)
from datetime import date, timedelta
from decimal import Decimal


# ============================================
# AUTHENTICATION FORMS
# ============================================

class UserRegistrationForm(UserCreationForm):
    """Enhanced user registration form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Enter your email address',
            'required': True
        })
    )
    
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'First Name',
            'required': True
        })
    )
    
    middle_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Middle Name (Optional)'
        })
    )
    
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Last Name',
            'required': True
        })
    )
    
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': '+1234567890',
            'required': True
        })
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'type': 'date',
            'required': True
        })
    )
    
    gender = forms.ChoiceField(
        choices=CustomUser.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200'
        })
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 resize-none',
            'rows': 3,
            'placeholder': 'Street Address'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'City'
        })
    )
    
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'State/Province'
        })
    )
    
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Postal Code'
        })
    )
    
    country = forms.CharField(
        max_length=100,
        initial='USA',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Country'
        })
    )
    
    referral_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Referral Code (Optional)'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Enter password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Confirm password'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'middle_name', 'last_name', 'phone_number',
            'date_of_birth', 'gender', 'address', 'city', 'state', 
            'postal_code', 'country', 'password1', 'password2'
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email.lower()
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise ValidationError('This phone number is already registered.')
        return phone
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            age = (date.today() - dob).days / 365.25
            if age < 18:
                raise ValidationError('You must be at least 18 years old to register.')
            if age > 120:
                raise ValidationError('Please enter a valid date of birth.')
        return dob
    
    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            if not CustomUser.objects.filter(referral_code=code).exists():
                raise ValidationError('Invalid referral code.')
        return code
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        
        # Handle referral
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code)
                user.referred_by = referrer
            except CustomUser.DoesNotExist:
                pass
        
        if commit:
            user.save()
            # Generate referral code for new user
            user.generate_referral_code()
        
        return user


class UserLoginForm(AuthenticationForm):
    """Custom login form"""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Email Address',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500 cursor-pointer'
        })
    )


class OTPVerificationForm(forms.Form):
    """OTP verification form for 2FA"""
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900 text-center text-2xl font-bold tracking-widest',
            'placeholder': 'Enter 6-digit OTP',
            'maxlength': '6',
            'pattern': '[0-9]{6}'
        })
    )


# ============================================
# PROFILE FORMS
# ============================================

class ProfileUpdateForm(forms.ModelForm):
    """User profile update form"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'middle_name', 'last_name', 'phone_number',
            'alternate_phone', 'address', 'address_line2', 'city', 
            'state', 'postal_code', 'country', 'gender', 'marital_status',
            'number_of_dependents', 'nationality', 'preferred_currency',
            'preferred_language', 'profile_image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'middle_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900', 'rows': 3}),
            'address_line2': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'postal_code': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'country': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'gender': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'marital_status': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'number_of_dependents': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'nationality': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'preferred_currency': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'preferred_language': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
        }


class EmploymentInformationForm(forms.ModelForm):
    """Employment information form"""
    
    class Meta:
        model = CustomUser
        fields = [
            'employment_status', 'employer_name', 'employer_phone',
            'employer_address', 'employment_type', 'job_title',
            'job_start_date', 'job_end_date', 'annual_income',
            'proof_of_employment', 'proof_of_income'
        ]
        widgets = {
            'employment_status': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'employer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'employer_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'employer_address': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900', 'rows': 3}),
            'employment_type': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'job_title': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'job_start_date': forms.DateInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900', 'type': 'date'}),
            'job_end_date': forms.DateInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900', 'type': 'date'}),
            'annual_income': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900', 'step': '0.01'}),
        }


class KYCDocumentForm(forms.ModelForm):
    """KYC document upload form"""
    
    class Meta:
        model = CustomUser
        fields = [
            'government_id_type', 'government_id_number', 'government_id_expiry',
            'front_id_image', 'back_id_image', 'proof_of_address'
        ]
        widgets = {
            'government_id_type': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'government_id_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'}),
            'government_id_expiry': forms.DateInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900', 'type': 'date'}),
        }
    
    def clean_government_id_expiry(self):
        expiry = self.cleaned_data.get('government_id_expiry')
        if expiry and expiry < date.today():
            raise ValidationError('Government ID has expired. Please provide a valid ID.')
        return expiry


class ChangePasswordForm(PasswordChangeForm):
    """Custom password change form"""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Current Password'
        })
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'New Password'
        })
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Confirm New Password'
        })
    )


# ============================================
# ACCOUNT FORMS
# ============================================


class AccountApplicationForm(forms.ModelForm):
    """Account application form"""
    
    class Meta:
        model = Account
        fields = ['account_type', 'account_name']
        widgets = {
            'account_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'required': True
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Account Name (Optional)'
            }),
        }
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        error_messages={
            'required': 'You must accept the account terms and conditions'
        }
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.user:
            # Check if user has verified KYC
            if not self.user.has_verified_kyc:
                raise ValidationError(
                    'You must complete KYC verification before opening an account.'
                )
            
            # Check if user already has too many accounts
            active_accounts = Account.objects.filter(
                customer=self.user
            ).exclude(status='CLOSED').count()
            
            if active_accounts >= 5:
                raise ValidationError(
                    'You have reached the maximum number of accounts allowed.'
                )
            
            # Check for duplicate account_type
            account_type = cleaned_data.get('account_type')
            
            if account_type:
                existing = Account.objects.filter(
                    customer=self.user,
                    account_type=account_type,
                ).exclude(status='CLOSED').exists()
                
                if existing:
                    raise ValidationError(
                        f'You already have a {dict(Account.ACCOUNT_TYPES).get(account_type)}. '
                        'Please choose a different account type.'
                    )
        
        return cleaned_data



class AccountActivationForm(forms.Form):
    """Account activation form with fee payment"""
    
    activation_receipt = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'accept': 'image/*,.pdf'
        }),
        help_text='Upload proof of payment for activation fee'
    )
    
    confirmation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='I confirm that I have paid the activation fee'
    )


# ============================================
# CARD FORMS
# ============================================

class CardApplicationForm(forms.ModelForm):
    """Card application form"""
    
    class Meta:
        model = Card
        fields = ['card_type', 'account', 'card_name']
        widgets = {
            'card_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'required': True
            }),
            'account': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'required': True
            }),
            'card_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Name as it appears on card',
                'required': True
            }),
        }
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        error_messages={
            'required': 'You must accept the card terms and conditions'
        }
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter accounts to only show user's active accounts (for card application)
        if self.user:
            self.fields['account'].queryset = Account.objects.filter(
                customer=self.user,
                status='ACTIVE'
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.user:
            # Check if user can apply for cards
            if not self.user.can_apply_for_cards:
                raise ValidationError(
                    'Your account is not eligible to apply for cards at this time.'
                )
            
            # Check if user has too many cards
            active_cards = Card.objects.filter(
                user=self.user,
                status__in=['PENDING', 'ACTIVE']
            ).count()
            
            if active_cards >= 10:
                raise ValidationError(
                    'You have reached the maximum number of cards allowed.'
                )
        
        return cleaned_data


class CardActivationForm(forms.Form):
    """Card activation form with fee payment"""
    
    activation_receipt = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'accept': 'image/*,.pdf'
        }),
        help_text='Upload proof of payment for card activation fee'
    )
    
    confirmation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='I confirm that I have paid the card activation fee'
    )


class CardPINForm(forms.Form):
    """Card PIN setup/change form"""
    
    new_pin = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': '4-digit PIN',
            'maxlength': '4',
            'pattern': '[0-9]{4}'
        })
    )
    
    confirm_pin = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Confirm PIN',
            'maxlength': '4',
            'pattern': '[0-9]{4}'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_pin = cleaned_data.get('new_pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        
        if new_pin and confirm_pin:
            if new_pin != confirm_pin:
                raise ValidationError('PINs do not match.')
            
            if not new_pin.isdigit():
                raise ValidationError('PIN must contain only numbers.')
        
        return cleaned_data


# ============================================
# TRANSACTION FORMS
# ============================================

class DepositForm(forms.Form):
    """Deposit form"""
    
    account = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'required': True
        }),
        label='Deposit To Account'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': '0.00',
            'step': '0.01',
            'required': True
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CASH', 'Cash Deposit'),
            ('CHECK', 'Check'),
            ('MOBILE_MONEY', 'Mobile Money'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'
        })
    )
    
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Transaction Reference (Optional)'
        })
    )
    
    receipt = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'accept': 'image/*,.pdf'
        }),
        help_text='Upload deposit receipt/proof'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'rows': 3,
            'placeholder': 'Additional notes (Optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Show all accounts except PENDING so the status-gate modal can inform the user
            self.fields['account'].queryset = Account.objects.filter(
                customer=self.user,
            ).exclude(status='PENDING')




class WithdrawalForm(forms.Form):
    """Withdrawal form"""
    
    account = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'required': True
        }),
        label='Withdraw From Account'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': '0.00',
            'step': '0.01',
            'required': True
        })
    )
    
    withdrawal_method = forms.ChoiceField(
        choices=[
            ('ATM', 'ATM Withdrawal'),
            ('BRANCH', 'Branch Withdrawal'),
            ('TRANSFER', 'Bank Transfer'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'rows': 3,
            'placeholder': 'Purpose of withdrawal (Optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Show all accounts except PENDING so the status-gate modal can inform the user
            self.fields['account'].queryset = Account.objects.filter(
                customer=self.user,
            ).exclude(status='PENDING')

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')
        
        if account and amount:
            symbol = account.customer.currency_symbol

            # Check if account has sufficient balance
            if amount > account.balance:
                raise ValidationError(
                    f'Insufficient funds. Available balance: {symbol}{account.balance}'
                )

            # Check daily withdrawal limit
            if amount > account.daily_withdrawal_limit:
                raise ValidationError(
                    f'Amount exceeds daily withdrawal limit of {symbol}{account.daily_withdrawal_limit}'
                )

            # Check minimum balance requirement
            if (account.balance - amount) < account.minimum_balance:
                raise ValidationError(
                    f'This withdrawal would bring your balance below the minimum required balance of {symbol}{account.minimum_balance}'
                )
        
        return cleaned_data



# ============================================
# TRANSFER FORMS
# ============================================

class TransferForm(forms.Form):
    """Fund transfer form"""
    
    from_account = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'required': True
        }),
        label='From Account'
    )
    
    beneficiary = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'
        }),
        label='Select Saved Beneficiary (Optional)'
    )
    
    beneficiary_account_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Account Number',
            'required': True
        })
    )
    
    beneficiary_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Beneficiary Name',
            'required': True
        })
    )
    
    beneficiary_bank = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Bank Name',
            'required': True
        })
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': '0.00',
            'step': '0.01',
            'required': True
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'rows': 3,
            'placeholder': 'Transfer description (Optional)'
        })
    )
    
    save_beneficiary = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='Save as beneficiary for future transfers'
    )
    
    beneficiary_nickname = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Beneficiary Nickname (Optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Show all accounts except PENDING so the status-gate modal can inform the user
            self.fields['from_account'].queryset = Account.objects.filter(
                customer=self.user,
            ).exclude(status='PENDING')
            self.fields['beneficiary'].queryset = Beneficiary.objects.filter(
                user=self.user
            ).order_by('-is_favorite', 'nickname')
    
    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        amount = cleaned_data.get('amount')
        
        if from_account and amount:
            # Check if user can make transfers
            if not self.user.can_make_transfers:
                raise ValidationError(
                    'Your account is not authorized to make transfers at this time.'
                )
            
            # Check if account has sufficient balance
            if not from_account.can_debit(amount):
                raise ValidationError(
                    f'Insufficient funds. Available balance: {from_account.balance}'
                )
            
            # Check daily transfer limit
            # if amount > from_account.daily_transfer_limit:
            #     raise ValidationError(
            #         f'Amount exceeds daily transfer limit of {from_account.daily_transfer_limit}'
            #     )
            
            # Check user's daily transfer limit
            # if amount > self.user.daily_transfer_limit:
            #     raise ValidationError(
            #         f'Amount exceeds your daily transfer limit of {self.user.daily_transfer_limit}'
            #     )
        
        return cleaned_data


# ============================================
# BENEFICIARY FORMS
# ============================================

class BeneficiaryForm(forms.ModelForm):
    """Add/Edit beneficiary form"""
    
    class Meta:
        model = Beneficiary
        fields = [
            'nickname', 'account_number', 'account_name', 'bank_name',
            'bank_code', 'routing_number', 'swift_code', 'is_favorite'
        ]
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'e.g., Mom, John Doe',
                'required': True
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Account Number',
                'required': True
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Account Name',
                'required': True
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Bank Name',
                'required': True
            }),
            'bank_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Bank Code (Optional)'
            }),
            'routing_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Routing Number (Optional)'
            }),
            'swift_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'SWIFT Code (Optional)'
            }),
            'is_favorite': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.user:
            account_number = cleaned_data.get('account_number')
            bank_name = cleaned_data.get('bank_name')
            
            # Check if beneficiary already exists (excluding current instance if editing)
            existing = Beneficiary.objects.filter(
                user=self.user,
                account_number=account_number,
                bank_name=bank_name
            )
            
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    'This beneficiary already exists in your saved beneficiaries.'
                )
        
        return cleaned_data


# ============================================
# SUPPORT TICKET FORMS
# ============================================

class SupportTicketForm(forms.ModelForm):
    """Support ticket creation form"""
    
    class Meta:
        model = SupportTicket
        fields = ['category', 'priority', 'subject', 'description']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'placeholder': 'Brief description of your issue',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
                'rows': 5,
                'placeholder': 'Please provide detailed information about your issue',
                'required': True
            }),
        }
    
    related_transaction = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900',
            'placeholder': 'Transaction ID (if applicable)'
        }),
        label='Related Transaction ID'
    )
    
    related_account = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 text-gray-900'
        }),
        label='Related Account'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['related_account'].queryset = Account.objects.filter(
                customer=self.user
            )


# ============================================
# NOTIFICATION FORMS
# ============================================

class NotificationPreferencesForm(forms.Form):
    """Notification preferences form"""
    
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='Email Notifications'
    )
    
    sms_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='SMS Notifications'
    )
    
    transaction_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='Transaction Alerts'
    )
    
    security_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='Security Alerts'
    )
    
    promotional_emails = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        }),
        label='Promotional Emails'
    )

    