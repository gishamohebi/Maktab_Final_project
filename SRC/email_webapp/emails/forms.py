from ckeditor.widgets import CKEditorWidget
from django import forms
from .models import *
from accounts.validators import *


# from pagedown.widgets import PagedownWidget


class NewEmailForm(forms.Form):
    receiver_to = forms.EmailField(validators=[valid_contact], required=False)
    receiver_cc = forms.CharField(widget=forms.TextInput, required=False)
    receiver_bcc = forms.CharField(widget=forms.TextInput, required=False)
    title = forms.CharField(max_length=50, required=False)
    text = forms.CharField(widget=CKEditorWidget(), required=False, )

    file = forms.FileField(
        validators=[file_size],
        required=False
    )


class FilterForm(forms.Form):
    username = forms.EmailField(validators=[valid_contact], required=False)
    subject = forms.CharField(max_length=50, required=False)
