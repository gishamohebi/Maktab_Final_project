from .views import *
from django.urls import path

urlpatterns = [
    path("", home, name="home"),
    path("register/", Register.as_view(), name="register"),
    path("login/", Login.as_view(), name="login"),
    path('activate/<uidb64>/<token>/', ActivateEmail.as_view(), name='activate'),
    path('phone/activate/', ActivatePhone.as_view(), name='activate_phone'),
    path("recover-link/", RecoverPassword.as_view(), name="recovery_link"),
    path("new-password/<uidb64>/", NewPassword.as_view(), name="recover"),
    path("logout/", logout_view, name="logout"),
    path("contacts/", ContactList.as_view(), name="contacts"),
    path("new-contact/", new_contact, name="new_email"),
    path("contact-detail/<int:pk>/", ContactDetail.as_view(), name="edit_contact"),
    path("update-contact/<int:pk>/", UpdateContact.as_view(), name="edit_contact"),
    path("delete-contact/<int:pk>/", delete_contact, name="delete_contact"),
    path('contact-new-email/<str:email>/', email_contact, name='email_contact')

]
