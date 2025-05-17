from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from datetime import date


# Create a custom user manager
# This manager is required when using AbstractBaseUser
class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, kakao_id=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given email or kakao_id.
        """
        # Users must have either an email or a Kakao ID
        if not (email or kakao_id):
            raise ValueError('Users must have an email address or a Kakao ID')

        # Normalize email if provided
        email = self.normalize_email(email) if email else None

        user = self.model(
            email=email,
            kakao_id=kakao_id,
            **extra_fields
        )

        # Set the password, even if not used for social login.
        # This is good practice for compatibility.
        # 유저가 직접 설정하는 것이 아니에요! 로그인에는 필요 없지만 설정은 필수
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Superusers must have an email address')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superusers are active by default

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password=password, **extra_fields)


class User(AbstractBaseUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    kakao_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, blank=True)
    blood_type = models.CharField(max_length=3, blank=True)
    profile_picture = models.URLField(blank=True)

    # Required fields for AbstractBaseUser to work with Django's auth system
    # is_active is used to determine if a user account is currently enabled.
    is_active = models.BooleanField(default=True)
    # is_staff is used to grant access to the Django admin site.
    is_staff = models.BooleanField(default=False)
    # is_superuser is used for full administrative privileges.
    is_superuser = models.BooleanField(default=False)

    # Link the custom manager to the model
    objects = CustomUserManager()

    # Define the field used as the unique identifier for authentication
    # when logging in via Django's standard login views or createsuperuser.
    # Since email is the only field likely to be used in a command-line login
    # or admin login, we'll use it here. Social logins use email or kakao_id
    # for lookup before calling login().
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS lists fields that are prompted for when creating a user
    # via the createsuperuser command. Since email is USERNAME_FIELD, it's not listed here.
    # We don't have other fields that must be prompted for by createsuperuser.
    REQUIRED_FIELDS = []

    # The 'password' and 'last_login' fields are provided automatically by AbstractBaseUser

    @property
    def age(self):
        if self.birthdate:
            today = date.today()
            age = today.year - self.birthdate.year
            if today.month < self.birthdate.month or (today.month == self.birthdate.month and today.day < self.birthdate.day):
                age -= 1
            return age
        return None

    # Required methods for AbstractBaseUser for permissions and admin compatibility
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always for superusers
        return self.is_superuser

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always for superusers who have is_staff=True
        return self.is_staff


    def __str__(self):
        """String representation of the User."""
        # Prioritize nickname, then email, then Kakao ID
        return self.nickname or self.email or f"Kakao:{self.kakao_id}"