import json
import os
import sys

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncMonth

from .models import *
from django.contrib import admin
from emails.models import *
from django.contrib.auth.admin import UserAdmin

admin.site.register(Contacts)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "send_emails", "received_emails")

    readonly_fields = ("send_emails", "received_emails")

    # fields = readonly_fields

    # list_filter = ("username",)

    def send_emails(self, obj):
        from django.db.models import Avg
        result = Emails.objects.filter(sender=obj).count()
        return result

    def received_emails(self, obj):
        from django.db.models import Avg
        result = Emails.objects.filter(receiver=obj).count()
        return result

    def changelist_view(self, request, extra_context=None):
        # Aggregate new subscribers per month
        emails_with_file = Emails.objects.filter(file__isnull=False).exclude(file='')

        usernames = []
        for email in emails_with_file:
            usernames.append(User.objects.get(pk=email.sender_id))
        usernames = set(usernames)
        usernames = list(usernames)

        file_data = []
        for user in usernames:
            files_of_user = emails_with_file.filter(sender_id=user.id)
            total = sum(int(objects.get_file_size) for objects in files_of_user)
            file_data.append({"user": user.username, "user_size": total})

        chart_data = (
            User.objects.annotate(date=TruncMonth("date_joined"))
                .values("date")
                .annotate(y=Count("id"))
                .order_by("-date")
        )

        # Serialize and attach the chart data to the template context
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        print(as_json)
        extra_context = extra_context or {"new_users_chart": as_json, 'file_data': file_data}

        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)
