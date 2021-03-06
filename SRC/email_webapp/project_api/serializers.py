from rest_framework import serializers
from emails.models import *
from accounts.models import *


class EmailsSerializer(serializers.HyperlinkedModelSerializer):
    sender = serializers.StringRelatedField(read_only=True, required=False)
    receiver = serializers.StringRelatedField(many=True, read_only=True, required=False)
    url = serializers.HyperlinkedIdentityField(view_name="email_detail_api")

    class Meta:
        model = Emails
        fields = ['url', 'id', 'title', 'text', 'sender', 'pub_date', 'receiver']


class ContactsSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.StringRelatedField(read_only=True, required=False)
    url = serializers.HyperlinkedIdentityField(view_name="contact_detail_api")

    class Meta:
        model = Contacts
        fields = ['url', 'id', 'name', 'email', 'owner']
