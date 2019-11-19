"""
User related models.

Users are split into the User and the Profile model. The User model focuses on the authentication
aspects while the Profile model contains all additional information. The Profile model uses a
one-to-one reference to the User model.
"""
import uuid
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    A custom user manager to deal with emails as unique identifiers for auth
    instead of usernames.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Creates and saves a User with the given email and password."""
        if not email:
            raise ValueError("The email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create a superuser with thegiven email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """User model."""

    username = None
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify a user.",
    )
    email = models.EmailField(_("email address"), unique=True, null=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user is part of the site staff"),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts"
        ),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Returns a user's full name if set, else their email."""
        try:
            if self.profile.full_name == "":
                return self.email
            else:
                return self.profile.full_name
        except Profile.DoesNotExist:
            return self.email

    def get_short_name(self):
        """Returns a user's short name if set, else their email."""
        try:
            if self.profile.short_name == "":
                return self.email
            else:
                return self.profile.short_name
        except Profile.DoesNotExist:
            return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Profile(models.Model):
    """Additional user information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,)

    short_name = models.CharField(
        _("short name"),
        max_length=30,
        blank=True,
        help_text=_("The name the user would like to be called."),
    )
    full_name = models.CharField(
        _("full name"),
        max_length=150,
        blank=True,
        help_text=_(
            "Stores a user's full name. Useful due to significant variations"
            " in local naming schemes."
        ),
    )
    date_joined = models.DateTimeField(
        _("date joined"),
        default=timezone.now,
        help_text=_("The date when a user joined."),
    )

    def __str__(self):
        return self.full_name
