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
    path("logout/", logout_view, name="logout")

]
