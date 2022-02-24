from django.core.exceptions import ValidationError
from django.contrib.auth.validators import UnicodeUsernameValidator
import re

username_validator = UnicodeUsernameValidator()


def valid_username(user_name):
    """
    check if the entered username ends without domain
    """
    result = re.search('@gmz.com$', user_name)
    if result is not None:
        raise ValidationError('Username must end without domain ')


def valid_contact(email_address):
    """
    check if the contact username is able
    """
    result = re.search('@gmz.com$', email_address)
    if result is None:
        raise ValidationError('The user name need the domain')


def valid_email(email):
    """
    check if the email address is valid
    """
    result = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.com\b', email)
    if result is None:
        raise ValidationError("The email you entered is not valid")


def valid_phone(phone):
    if " " in phone:
        raise ValidationError("Space is not a valid character")
    if len(phone) < 11:
        raise ValidationError("Enter phone number like 09123456789")
