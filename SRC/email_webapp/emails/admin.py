import json

from django.contrib import admin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth
from django.http import JsonResponse
from django.urls import path

from .models import *

# Register your models here.
# admin.site.register(user)
admin.site.register(Category)

admin.site.register(Signature)


@admin.register(Emails)
class EmailsAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "title", "pub_date")  # display these table columns in the list view
    ordering = ("-pub_date",)
    date_hierarchy = "pub_date"

    def changelist_view(self, request, extra_context=None):
        chart_data = (
            Emails.objects.annotate(date=TruncMonth("pub_date"))
                .values("date")
                .annotate(y=Count("id"))
                .order_by("-date")
        )
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        extra_context = extra_context or {"chart_data": as_json}
        return super().changelist_view(request, extra_context=extra_context)
