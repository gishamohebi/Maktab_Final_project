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
    path('add-archive/<int:pk>/', add_archive, name="add_archive"),
    path('add-trash/<int:pk>/', add_trash, name="add_trash"),

]
