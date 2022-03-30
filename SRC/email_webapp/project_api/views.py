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


# Create your views here.


# class ListEmails(generics.ListCreateAPIView):
#     serializer_class = EmailsSerializer
#
#     def get_queryset(self):
#         user = authenticate(username=self.kwargs['username'], password=self.kwargs['password'])
#         if user:
#             login(self.request, user)
#             return Emails.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))
#         else:
#             raise Http404


class EmailDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmailsSerializer

    def get_queryset(self):
        return Emails.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))


# class ListContacts(generics.ListCreateAPIView):
#     serializer_class = ContactsSerializer
#
#     def get_queryset(self):
#         user = authenticate(username=self.kwargs['username'], password=self.kwargs['password'])
#         if user:
#             login(self.request, user)
#             return Contacts.objects.filter(owner=user)
#         else:
#             raise Http404


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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
       return Contacts.objects.filter(owner=self.request.user)
