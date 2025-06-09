# login/models.py

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from datetime import date, timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, kakao_id=None, password=None, **extra_fields):
        if not (email or kakao_id):
            raise ValueError('Users must have an email address or a Kakao ID')

        email = self.normalize_email(email) if email else None

        user = self.model(
            email=email,
            kakao_id=kakao_id,
            **extra_fields
        )

        # --- FIX: Only attempt to set password if it's provided and not None/empty ---
        # This makes the user creation more robust if password is truly optional.
        if password: # Check if password is not None and not an empty string
            user.set_password(password)
        else:
            user.set_unusable_password() # Set an unusable password if none is provided
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Superusers must have an email address')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # --- FIX: Ensure superuser creation also handles password as potentially None ---
        return self.create_user(email, password=password, **extra_fields)


class User(AbstractBaseUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    kakao_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, blank=True)
    blood_type = models.CharField(max_length=3, blank=True)
    profile_picture_key = models.URLField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    # --- FIX: Ensure 'password' is NOT in REQUIRED_FIELDS if you're not using it ---
    # This list is for fields prompted when creating a user via createsuperuser, etc.
    REQUIRED_FIELDS = [] 

    @property
    def age(self):
        if self.birthdate:
            today = date.today()
            age = today.year - self.birthdate.year
            if today.month < self.birthdate.month or (today.month == self.birthdate.month and today.day < self.birthdate.day):
                age -= 1
            return age
        return None

    def get_profile_picture_url(self):
        return self.profile_picture_key

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_staff

    def __str__(self):
        return self.nickname or self.email or f"Kakao:{self.kakao_id}"