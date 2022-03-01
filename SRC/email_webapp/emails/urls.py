from django.urls import path
from .views import *

urlpatterns = [
    path("inbox/", InboxList.as_view(), name="inbox"),
    path("sent/", SentList.as_view(), name="sent"),
    path("draft/", DraftList.as_view(), name="draft"),
    path("trash/", TrashList.as_view(), name="trash"),
    path("contacts/", ContactList.as_view(), name="contacts"),
    path("new-email/", new_email, name="new_email"),
    path("new-contact/", new_contact, name="new_email"),

]
