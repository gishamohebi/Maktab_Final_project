from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import Http404
from rest_framework import generics
from rest_framework.authentication import *
from rest_framework.permissions import IsAuthenticated

from .serializers import *
from django.http import JsonResponse
from emails.models import *
from accounts.models import *


class EmailDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmailsSerializer

    def get_queryset(self):
        return Emails.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))


class ContactDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactsSerializer

    def get_queryset(self):
        return Contacts.objects.filter(owner=self.request.user)


class ListEmails(generics.ListCreateAPIView):
    serializer_class = EmailsSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Emails.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))


class ListContacts(generics.ListCreateAPIView):
    serializer_class = ContactsSerializer
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contacts.objects.filter(owner=self.request.user)
