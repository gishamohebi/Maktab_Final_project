from django.contrib.auth.base_user import AbstractBaseUser
from .validators import *
from accounts.models import *
from django.contrib.auth.models import AbstractUser


# Create your models here.

class Category(models.Model):
    title = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )


class Signature(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
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
        related_name="receiver"
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
        upload_to="%Y/%m_%d/",
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
    is_sent = models.BooleanField(default=False)
    is_inbox = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    is_trash = models.BooleanField(default=False)
