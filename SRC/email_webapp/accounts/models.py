from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from .validators import *


class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        validators=[valid_username, username_validator],
        help_text=_('Required 150 characters or fewer.Letters, digits and @/./+/-/_ only'),
        error_messages=
        {
            'unique': _("A user with that username already exists.")
        },
    )
    birth_date = models.DateTimeField(
        blank=True,
        null=True
    )
    gender_choice = [
        ("F", "Female"),
        ("M", "Male"),
        ("O", "Other")
    ]
    gender = models.CharField(
        max_length=1,
        choices=gender_choice,
        blank=True,
        null=True
    )
    recovery_choice = [
        ("Email", "Email"),
        ("Phone", "Phone")
    ]
    recovery = models.CharField(
        max_length=5,
        choices=recovery_choice,
        blank=False,
        null=False,
        help_text="This field is for recovering and validations"
    )
    email_address = models.CharField(
        _('email address'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        validators=[valid_email],
        error_messages={
            "unique": "This email already has an account "
        }
    )
    phone = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        null=True,
        validators=[valid_phone],
        error_messages={
            'unique': "This phone number already has an account"
        }
    )
    active_email = models.BooleanField(default=False)
    active_phone = models.BooleanField(default=False)
    country = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    slug = models.SlugField(
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.username)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Contacts(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        validators=[valid_contact]
    )
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False
    )
    birth_date = models.DateTimeField(
        null=True,
        blank=True
    )
    emails = models.TextField(
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=12,
        blank=True,
        null=False,
    )
    slug = models.SlugField(
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class OtpCode(models.Model):
    phone_number = models.CharField(max_length=12)
    code = models.PositiveSmallIntegerField()
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.phone_number} - {self.code} - {self.created}'
