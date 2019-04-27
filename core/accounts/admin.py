from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Profile
from .forms import UserRegistrationForm


class ProfileInline(admin.StackedInline):
    """Profile of a user."""

    model = Profile
    can_delete = False
    verbose_name_plural = "profile"
    fk_name = "user"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    add_form = UserRegistrationForm

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    inlines = [ProfileInline]

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = ("email", "is_staff")
    search_fields = ("email", "profile__short_name", "profile__full_name")
    ordering = ("email",)
