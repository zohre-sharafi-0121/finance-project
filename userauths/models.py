from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True) 
    username = models.CharField(unique=True, max_length=50)
    transaction_pin = models.CharField(max_length=128, blank=True, null=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email   

class KYC(models.Model):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = 'UNVERIFIED', 'Unverified'
        PENDING = 'PENDING', 'Pending Review'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    class IDType(models.TextChoices):
        NATIONAL_ID = 'NATIONAL_ID', 'National ID Card'
        DRIVERS_LICENSE = 'DRIVERS_LICENSE', "Driver's License"
        PASSPORT = 'PASSPORT', 'International Passport'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="kyc_profile")
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED)
    id_type = models.CharField(max_length=28, choices=IDType.choices, default=IDType.NATIONAL_ID)
    id_image = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KYC for {self.user.email}"
    
    class Meta:
        verbose_name = "KYC Record"
        verbose_name_plural = "KYC Records"
        ordering = ['-created_at']
