from django.contrib.auth import authenticate, login
from django.http import Http404
from rest_framework import generics
from .serializers import *

from emails.models import *
from accounts.models import *


# Create your views here.


class ListEmails(generics.ListCreateAPIView):
    serializer_class = EmailsSerializer

    def get_queryset(self):
        user = authenticate(username=self.kwargs['username'], password=self.kwargs['password'])
        if user:
            login(self.request, user)
            return Emails.objects.filter(sender=user)
        else:
            raise Http404


class EmailDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmailsSerializer

    def get_queryset(self):
        return Emails.objects.filter(sender=self.request.user)


class ListContacts(generics.ListCreateAPIView):
    serializer_class = ContactsSerializer

    def get_queryset(self):
        user = authenticate(username=self.kwargs['username'], password=self.kwargs['password'])
        if user:
            login(self.request, user)
            return Contacts.objects.filter(owner=user)
        else:
            raise Http404


class ContactDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactsSerializer

    def get_queryset(self):
        return Contacts.objects.filter(owner=self.request.user)
