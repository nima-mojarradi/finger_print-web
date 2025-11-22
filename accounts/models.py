from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

ROLES_OPTIONS = (
    ('super_admin', 'Super Admin'),
    ('normal_admin', 'Normal Admin'),
    ('user', 'User'),
)

FINGER_NAMES = (
    ('right_thumb', 'Right Thumb'),
    ('right_pointer', 'Right Pointer'),
    ('right_middle', 'Right Milddle'),
    ('right_ring', 'Right Ring'),
    ('right_pinky', 'Right Pinky'),
    ('left_thumb', 'Left Thumb'),
    ('left_pointer', 'Left Pointer'),
    ('left_middle', 'Left Middle'),
    ('left_ring', 'Left Ring'),
    ('left_pinky', 'Left Pinky')
)

class CustomUserManager(BaseUserManager):

    def make_random_password(self, length=10):
        return get_random_string(length=length)
    def create_user(self, nationality_number, first_name, last_name, password=None, **extra_fields):
        if not nationality_number:
            raise ValueError("User must have a nationality number")

        user = self.model(
            nationality_number=nationality_number,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )

        if not password:
            password = get_random_string(length=10)
            user.set_password(password)

            if hasattr(user, "email") and user.email:
                try:
                    send_mail(
                        subject="رمز موقت حساب شما",
                        message=f"سلام {user.first_name}!\n\nرمز موقت شما برای ورود به سیستم: {password}\nلطفاً پس از ورود آن را تغییر دهید.",
                        from_email="no-reply@yourdomain.com",
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print("Email send error:", e)
        else:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, nationality_number, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('roles', 'super_admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(
            nationality_number, first_name, last_name, password, **extra_fields
        )

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    nationality_number = models.CharField(max_length=10, primary_key=True)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, blank=True)
    roles = models.CharField(max_length=250, choices=ROLES_OPTIONS)

    USERNAME_FIELD = 'nationality_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'company', 'roles', 'email']

    objects = CustomUserManager()

    class Meta:
        ordering = ['company']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Address(models.Model):
    title = models.CharField(max_length=250)
    address = models.TextField(unique=True)
    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
    def __str__(self):
        return self.title


class Company(models.Model):
    title = models.CharField(max_length=250)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        constraints = [
            models.UniqueConstraint(fields=['title', 'address'], name='unique_title_address')
        ]
    def __str__(self):
        return self.title

class Fingerprint(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='fingerprints')
    finger_name = models.CharField(max_length=50, blank=True, null=True, choices=FINGER_NAMES) 
    template_data = models.BinaryField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} - {self.finger_name or 'Unnamed Finger'}"