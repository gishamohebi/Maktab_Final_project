from django.urls import path

from . import views

urlpatterns = [
    path('<str:username>/<str:password>/emails/', views.ListEmails.as_view()),
    path('<str:username>/<str:password>/contacts/', views.ListContacts.as_view()),
    path('email_detail/<int:pk>/', views.EmailDetail.as_view(), name='email_detail_api'),
    path('contact_detail/<int:pk>/', views.ContactDetail.as_view(), name='contact_detail_api'),
]