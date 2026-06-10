from django.contrib import admin
from django.db.models import Sum
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Wallet, Transaction, Beneficiary, 
    Notification, SavingsGoal
)


# ====================== INLINES ======================
class TransactionInline(TabularInline):
    """Shows recent transactions directly on the Wallet page."""
    model = Transaction
    extra = 0
    fields = ('timestamp', 'transaction_type', 'amount', 'status')
    readonly_fields = ('timestamp', 'transaction_type', 'amount', 'status')
    ordering = ('-timestamp',)
    verbose_name_plural = "Recent Transactions"
    tab = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SavingsGoalInline(TabularInline):
    """Shows savings goals directly on the Wallet page."""
    model = SavingsGoal
    extra = 0
    fields = ('name', 'target_amount', 'current_amount', 'progress_percentage')
    readonly_fields = ('progress_percentage',)
    verbose_name_plural = "Savings Goals"
    tab = True


# ====================== MODEL ADMINS ======================
@admin.register(Wallet)
class WalletAdmin(ModelAdmin):  # ← Now inherits from Unfold
    """Admin configuration for the Wallet model."""
    list_display = ('user', 'wallet_id', 'balance', 'created_at')
    # search_fields = ('user__username', 'user__email', 'wallet_id')
    # list_filter = ('created_at',)
    # readonly_fields = ('wallet_id', 'balance', 'created_at', 'updated_at')
    # list_select_related = ('user',)

    inlines = [TransactionInline, SavingsGoalInline]

    # # Optional: Make it look even nicer with Unfold options
    # list_fullwidth = True
    # compressed_fields = True


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):  # ← Unfold ModelAdmin
    """Admin configuration for the Transaction model."""
    list_display = ('reference', 'wallet_user', 'transaction_type', 'amount', 'status', 'timestamp')
    search_fields = ('reference', 'wallet__user__username', 'wallet__user__email', 'external_reference')
    list_filter = ('transaction_type', 'status', 'timestamp')
    readonly_fields = ('reference', 'timestamp')
    list_select_related = ('wallet__user',)

    fieldsets = (
        ('Transaction Details', {
            'fields': ('reference', 'wallet', 'transaction_type', 'amount', 'status')
        }),
        ('References', {
            'fields': ('external_reference',)
        }),
        ('Transfer Details', {
            'fields': ('sender', 'receiver'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    def wallet_user(self, obj):
        return obj.wallet.user
    wallet_user.short_description = 'User'


@admin.register(Beneficiary)
class BeneficiaryAdmin(ModelAdmin):
    """Admin configuration for the Beneficiary model."""
    list_display = ('user', 'beneficiary_user', 'created_at')
    search_fields = ('user__username', 'beneficiary_user__username')
    list_filter = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    """Admin configuration for the Notification model."""
    list_display = ('user', 'title', 'is_read', 'timestamp')
    search_fields = ('user__username', 'title', 'message')
    list_filter = ('is_read', 'timestamp')
    list_editable = ('is_read',)


@admin.register(SavingsGoal)
class SavingsGoalAdmin(ModelAdmin):
    """Admin configuration for the SavingsGoal model."""
    list_display = ('wallet_user', 'name', 'target_amount', 'current_amount', 'progress_percentage', 'target_date')
    search_fields = ('wallet__user__username', 'name')
    list_filter = ('target_date',)

    def wallet_user(self, obj):
        return obj.wallet.user
    wallet_user.short_description = 'User'