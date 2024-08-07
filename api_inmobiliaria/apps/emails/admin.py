from django.contrib import admin
from .models import Token


@admin.register(Token)
class TokenAdminPanel(admin.ModelAdmin):
    """
    Admin panel configuration for the Token model.
    """

    list_display = ["id", "token", "date_joined"]
    search_fields = ["token"]
    readonly_fields = ["date_joined", "id"]
    ordering = ["-date_joined"]
