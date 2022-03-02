from django import forms
from .models import *


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email_address",
            "phone",
            "first_name",
            "last_name",
            "birth_date",
            "recovery"
        ]

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class NewContact(forms.ModelForm):
    class Meta:
        model = Contacts
        fields = [
            'email',
            'name',
            'emails',
            'phone',
            'birth_date'
        ]
