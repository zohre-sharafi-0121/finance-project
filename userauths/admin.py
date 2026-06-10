from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import User, KYC


@admin.register(User)
class UserAdmin(ModelAdmin):
    """Custom User Admin with Unfold"""
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    
    list_fullwidth = True
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'transaction_pin')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KYC)
class KYCAdmin(ModelAdmin):
    """KYC Admin with Unfold"""
    
    list_display = ('user', 'full_name', 'verification_status', 'id_type', 'created_at')
    list_filter = ('verification_status', 'id_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'full_name')
    list_select_related = ('user',)
    
    # Unfold options
    list_fullwidth = True
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (None, {
            'fields': ('user', 'full_name', 'verification_status')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'id_type', 'id_image'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields