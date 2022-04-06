import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.contrib import admin
from emails.models import *

admin.site.register(Contacts)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "send_emails", "received_emails", "used_storage")

    readonly_fields = ("send_emails", "received_emails")

    @staticmethod
    def send_emails(obj):
        from django.db.models import Avg
        result = Emails.objects.filter(sender=obj).count()
        return result

    @staticmethod
    def received_emails(obj):
        from django.db.models import Avg
        result = Emails.objects.filter(receiver=obj).count()
        return result

    @staticmethod
    def used_storage(obj):
        emails_with_files = Emails.objects.filter(Q(sender=obj) | Q(receiver=obj)).exclude(file=None,
                                                                                           file__isnull=False)
        storage = sum(int(email.get_file_size) for email in emails_with_files if email.get_file_size)
        return storage

    def changelist_view(self, request, extra_context=None):
        # Aggregate new subscribers per month
        emails_with_file = Emails.objects.filter(file__isnull=False).exclude(file='')

        usernames = []
        for email in emails_with_file:
            usernames.append(User.objects.get(pk=email.sender_id))
            for receiver in email.receiver.filter():
                usernames.append(User.objects.get(pk=receiver.id))
        usernames = set(usernames)
        usernames = list(usernames)

        file_data = []
        for user in usernames:
            files_of_user = emails_with_file.filter(Q(sender_id=user.id) | Q(receiver=user))
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
        extra_context = extra_context or {"new_users_chart": as_json, 'file_data': file_data}

        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)
