from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

import uuid
from decimal import Decimal

class Beneficiary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="beneficiaries")
    beneficiary_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="benefactors")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "beneficiary_user")
        ordering = ['-created_at']


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wallet_id = models.CharField(max_length=10, unique=True, editable=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s wallet {self.wallet_id}"
    
    def save(self, *args, **kwargs):
        if not self.wallet_id:
            self.wallet_id = str(uuid.uuid4().int)[:10]
        super().save(*args, **kwargs)

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        TRANSFER = 'TRANSFER', 'Transfer'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        SAVINGS = 'SAVINGS', 'Savings'

    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default="0.00")
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    external_reference = models.CharField(max_length=20, blank=True, null=True)
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="sent_transactions", blank=True, null=True)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="received_transactions", blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.wallet.user.username} - {self.status}"
    

class Notification(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        TRANSFER = 'TRANSFER', 'Transfer'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        SAVINGS = 'SAVINGS', 'Savings'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TransactionType.choices, default=None)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
    
class SavingsGoal(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)

    def __str__(self):
        return f"'{self.name}' goal for {self.wallet.user.username}"

    @property
    def progress_percentage(self):
        """Calculate progress percentage safely."""
        if not self.target_amount or self.target_amount <= 0:
            return 0  # or "N/A" if you prefer
        
        if not self.current_amount:
            return 0
        
        percentage = (self.current_amount / self.target_amount) * 100
        return min(round(percentage, 2), 100)  # Cap at 100%