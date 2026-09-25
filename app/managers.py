from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of username.
    """
    
    def create_user(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, name, phone and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not first_name:
            raise ValueError(_('The First Name field must be set'))
        if not last_name:
            raise ValueError(_('The Last Name field must be set'))
        if not phone_number:
            raise ValueError(_('The Phone Number field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, name, phone and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('has_verified_kyc', True)
        extra_fields.setdefault('email_verified', True)
        extra_fields.setdefault('phone_verified', True)
        extra_fields.setdefault('account_status', 'Active')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, first_name, last_name, phone_number, password, **extra_fields)
    
    def get_by_natural_key(self, email):
        """
        Get user by email (natural key)
        """
        return self.get(**{self.model.USERNAME_FIELD: email})