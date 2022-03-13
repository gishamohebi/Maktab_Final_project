from django.urls import path
from .views import *
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("inbox/", InboxList.as_view(), name="inbox"),
    path("sent/", SentList.as_view(), name="sent"),
    path("draft/", DraftList.as_view(), name="draft"),
    path("trash/", TrashList.as_view(), name="trash"),
    path("archive/", ArchiveList.as_view(), name="archive"),
    path("new-email/", new_email, name="new_email"),
    path("edit-draft/<int:pk>/", edit_draft, name="edit-draft"),
    path('email-detail/<int:pk>', EmailDetail.as_view(), name="email_detail"),
    path('check-archive/<int:pk>/', check_archive, name="add_archive"),
    path('check-trash/<int:pk>/', check_trash, name="add_trash"),
    path('label/<int:pk>/', LabelEmailList.as_view(), name="label_email"),
    path('set-label/<int:pk>/', set_label, name="set_label"),
    path('remove-label/<int:pk>/', remove_from_label, name="remove_label"),
    path('new-label/', new_label, name="new_label"),
    path('delete-label/', delete_label, name="delete_label"),
    path('new-signature/', new_signature, name="new_signature"),
    path('delete-signature/', delete_signature, name="delete_signature"),
    path('reply-email/<int:pk>/', reply_email, name="reply_email"),
    path('download-file/<str:filename>/', download_file, name="download_file"),
    path('forward-email/<int:pk>/', forward_email, name="forward_email"),
    path('search-email/', csrf_exempt(search_email), name="search_email"),

]
