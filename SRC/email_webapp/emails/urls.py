from django.urls import path
from .views import *

urlpatterns = [
    path("inbox/", InboxList.as_view(), name="inbox"),
    path("sent/", SentList.as_view(), name="sent"),
    path("draft/", DraftList.as_view(), name="draft"),
    path("trash/", TrashList.as_view(), name="trash"),
    path("archive/", ArchiveList.as_view(), name="archive"),
    path("new-email/", new_email, name="new_email"),
    path('email-detail/<int:pk>', EmailDetail.as_view(), name="email_detail"),
    path('check-archive/<int:pk>/', check_archive, name="add_archive"),
    path('check-trash/<int:pk>/', check_trash, name="add_trash"),
    path('label/<int:pk>/', LabelEmailList.as_view(), name="label_email"),
    path('new-label/', new_label, name="new_label"),
    path('delete-label/', delete_label, name="new_label"),

]
