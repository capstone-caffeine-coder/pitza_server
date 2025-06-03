from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from datetime import date


class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, kakao_id=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given email or kakao_id.
        """
        # Users must have either an email or a Kakao ID
        if not (email or kakao_id):
            raise ValueError('Users must have an email address or a Kakao ID')

        email = self.normalize_email(email) if email else None

        user = self.model(
            email=email,
            kakao_id=kakao_id,
            **extra_fields
        )

        # 유경: 유저가 직접 설정하는 것이 아니에요! 로그인에는 필요 없지만 설정은 필수
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
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
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
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


    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return self.is_superuser

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return self.is_staff


    def __str__(self):
        """String representation of the User."""
        return self.nickname or self.email or f"Kakao:{self.kakao_id}"