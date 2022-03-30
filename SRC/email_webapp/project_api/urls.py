from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    # path('<str:username>/<str:password>/emails/', views.ListEmails.as_view()),
    # path('<str:username>/<str:password>/contacts/', views.ListContacts.as_view()),
    path('email_detail/<int:pk>/', views.EmailDetail.as_view(), name='email_detail_api'),
    path('contact_detail/<int:pk>/', views.ContactDetail.as_view(), name='contact_detail_api'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('emails/', views.ListEmails.as_view()),
    path('contacts/', views.ListContacts.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
