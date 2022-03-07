from django.contrib.auth.base_user import AbstractBaseUser
from .validators import *
from accounts.models import *
from django.contrib.auth.models import AbstractUser


# Create your models here.

class Category(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    title = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ["owner", "title"]

    def __str__(self):
        return self.title


class Signature(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    text = models.TextField(
        blank=False,
        default=f"{owner}"
    )

    def __str__(self):
        return self.text


class Emails(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING
    )
    receiver = models.ManyToManyField(
        User,
        related_name="receiver",

    )
    receiver_to = models.ManyToManyField(
        User,
        related_name="receiver_to",

    )
    receiver_cc = models.ManyToManyField(
        User,
        related_name="receiver_cc",

    )
    receiver_bcc = models.ManyToManyField(
        User,
        related_name="receiver_bcc",
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
    )
    category = models.ManyToManyField(
        Category,
        blank=True
    )
    title = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    text = models.TextField(
        blank=True,
        null=True
    )
    file = models.FileField(
        upload_to='',
        validators=[file_size],
        null=True,
        blank=True
    )
    signature = models.ForeignKey(
        Signature,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
    )
    pub_date = models.DateTimeField(
        auto_now=True
    )
    status_choice = [
        ("send", "send"),
        ("draft", "draft"),

    ]
    status = models.CharField(
        max_length=5,
        choices=status_choice,
        null=False,
        blank=False,
        default=None
    )
    is_trash = models.BooleanField(default=False)
    is_archive = models.BooleanField(default=False)
    is_cc = models.BooleanField(default=False)
    is_bcc = models.BooleanField(default=False)
    is_to = models.BooleanField(default=False)

    def __str__(self):
        return self.status

    class Meta:
        ordering = ['-pub_date']
