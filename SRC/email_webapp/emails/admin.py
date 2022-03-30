import json
from django.db import IntegrityError
from django.contrib import admin
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder

from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import path

from .models import *

# Register your models here.
# admin.site.register(user)

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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ('title',)
    list_display = ['owner', 'title']

    def add_view(self, request):
        if request.method == "POST":
            try:
                users = User.objects.all()
                for user in users:
                    Category.objects.create(owner_id=user.pk, title=request.POST.get('title'))
                return HttpResponseRedirect("/admin/emails/category/")
            except Exception as e:
                messages.add_message(request, messages.ERROR, message="This label exist")
                return HttpResponseRedirect("/admin/emails/category/add/")

        return super(CategoryAdmin, self).add_view(request)
