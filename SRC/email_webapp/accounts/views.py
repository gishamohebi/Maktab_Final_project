import csv
import json
import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.views.generic import DetailView, UpdateView

from .tokens import account_activation_token
from utils import send_otp_code, send_recover_link
from emails.forms import *
from emails.views import BaseList
from emails.extera_handeler import creat_draft
from .forms import *
import logging

logger = logging.getLogger('accounts')


def home(request):
    # todo: make a template to error when they are login
    # if request.user.is_authenticated:
    #     return HttpResponse("No")
    return render(request, "users/home.html")


def send_validation_email(request, user):
    user.active_email = False
    user.save()
    current_site = get_current_site(request)  # to get domain of the site
    subject = 'Activate Your Account'
    message = render_to_string(
        'users/account_activation_email.html',
        {'user': user,
         'domain': current_site.domain,
         'uid': urlsafe_base64_encode(force_bytes(user.pk)),
         # A unique identifier is an identifier that is guaranteed
         # to be unique among all identifiers a kind of readable hash
         'token': account_activation_token.make_token(user),
         }
    )
    send_mail(subject, message, "gisha.mohebi@gmail.com", [user.email_address], fail_silently=False)


class Register(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "users/register_form.html", {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        form.email_address = request.POST.get("email_address")
        form.phone = request.POST.get("phone")
        form.recovery = request.POST.get("recovery")
        form.birth_date = request.POST.get("birth_date")
        try:
            if form.is_valid():

                try:
                    user = form.save(commit=False)  # Do not save to table yet
                    user.username += "@gmz.com"
                    validate_password(form.cleaned_data['password'], user)
                except ValidationError as e:
                    messages.add_message(request, messages.ERROR, message=''.join(e))
                    return redirect('register')

                if form.email_address is not None:
                    form.save()
                    send_validation_email(request, user)
                    messages.add_message(
                        request, messages.SUCCESS,
                        'We sent you an email to verify your account')
                    return HttpResponseRedirect("/accounts/login/")
                if form.phone is not None:
                    request.session['registration_info'] = {
                        'username': form.cleaned_data['username'] + "@gmz.com",
                        'phone': form.cleaned_data['phone'],
                        'email': form.cleaned_data['email_address'],
                        'first_name': form.cleaned_data['first_name'],
                        'last_name': form.cleaned_data['last_name'],
                        'birth_date': form.cleaned_data['birth_date'],
                        'password': form.cleaned_data['password'],
                        'recovery': form.cleaned_data['recovery']
                    }

                    random_code = random.randint(1000, 9999)
                    send_otp_code(user.phone, random_code)
                    OtpCode.objects.create(phone_number=form.cleaned_data['phone'], code=random_code)
                    messages.add_message(request, messages.INFO,
                                         "We sent your phone a verify code,enter it please")
                    return redirect(f"/accounts/phone/activate/")
        except IntegrityError:
            messages.add_message(request, messages.ERROR, message="This username exist")
            return redirect('register')

        else:
            messages.add_message(request, messages.ERROR, message=form.errors)
            return redirect('register')


class Login(View):
    def get(self, request):
        # todo: make a template to error when they are login
        # if request.user.is_authenticated:
        #     return HttpResponse("Your already log in")
        return render(request, "users/login.html")

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:

            if user.email_address:
                if user.active_email is False:
                    messages.add_message(
                        request, messages.ERROR,
                        'Email is not verified, please check your email inbox')
                    logger.error(f"User with username {username} did not verify email")
                    return redirect("login")
            login(request, user)
            return HttpResponseRedirect("/gmz-email/inbox/")

        messages.add_message(
            request, messages.ERROR,
            'wrong username or password')
        logger.error(f"Wrong info were entered username : {username} , password : {password}")
        return redirect("login")


@login_required(redirect_field_name='login')
def logout_view(request):
    if request.method == 'GET':
        logout(request)
        return redirect("/accounts/login/")


class ActivateEmail(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))  # convert a kind of hash to str
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token) \
                and user.active_email is False:
            user.active_email = True
            user.save()
            login(request, user)
            default_categories = Category.objects.filter(owner__in=User.objects.filter(is_superuser=True))
            for cat in default_categories:
                Category.objects.create(owner=user, title=cat.title)
            messages.success(request, (f"Your account have been confirmed."
                                       f"Your username is {user.username}"))
            return redirect("login")
        else:
            messages.warning(request, (
                'The confirmation link was invalid,'
                ' possibly because it has already been used.'
            ))
            return redirect("login")


class ActivatePhone(View):
    def get(self, request):
        return render(request, "users/account_activation_phone.html")

    def post(self, request):
        registered = request.session['registration_info']
        code = OtpCode.objects.get(phone_number=registered['phone'])
        verify = request.POST.get("code")
        if verify == str(code.code):
            user = User(
                username=registered["username"],
                email_address=registered["email"],
                phone=registered["phone"],
                birth_date=registered["birth_date"],
                first_name=registered["first_name"],
                last_name=registered["last_name"],
                active_phone=True,
                recovery=registered["recovery"]
            )
            user.set_password(registered["password"])
            user.save()
            code.delete()
            default_categories = Category.objects.filter(owner__in=User.objects.filter(is_superuser=True))
            for cat in default_categories:
                Category.objects.create(owner=user, title=cat.title)
            messages.success(request, (f"Your account have been confirmed."
                                       f"Your username is {user.username}"))
            return redirect("login")

        messages.add_message(request, messages.ERROR, "The verify code is wrong")
        return redirect("activate_phone")


def send_recovery_link(request, user):
    current_site = get_current_site(request)  # to get domain of the site
    uid_ = urlsafe_base64_encode(force_bytes(user.pk))
    if user.recovery == "Email":
        subject = 'Recover Your Password'
        message = render_to_string(
            'users/email_recover_link.html',
            {'user': user,
             'domain': current_site.domain,
             'uid': uid_
             })
        send_mail(subject, message,
                  "gisha.mohebi@gmail.com", [user.email_address], fail_silently=False)
    if user.recovery == "Phone":
        link = f"http://{current_site.domain}/accounts/new-password/{uid_}/"
        send_recover_link(user.phone, link)


class RecoverPassword(View):
    def get(self, request):
        return render(request, "users/recover_request.html")

    def post(self, request):
        username = request.POST.get("username")
        try:
            user = User.objects.get(username=username)
            if user:
                if user.recovery == "Email":
                    if user.active_email is True:
                        send_recovery_link(request, user)
                        message = "We sent your email recover link please check."
                    else:
                        message = "You didn't verify your email!"
                        logger.error(f"user with username {username} did not verify email")
                else:
                    send_recovery_link(request, user)
                    message = "We sent your phone the recover link please check."
        except ObjectDoesNotExist:
            message = "This username dose not exist."
            messages.add_message(request, messages.ERROR, message=message)
            logger.error(f"Wrong username for recovering password : {username}")
            return redirect("recovery_link")
        messages.add_message(request, messages.INFO, message=message)
        return redirect("login")


class NewPassword(View):
    def get(self, request, uidb64, *args, **kwargs):
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        return render(request, "users/new_password.html", {"user": user})

    def post(self, request, uidb64):
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        try:
            password = request.POST.get("password")
            validate_password(password, user)
        except ValidationError as e:
            for _e in e:
                messages.add_message(request, messages.ERROR, message=_e)
            return render(request, "users/new_password.html", {"user": user.username})
        else:
            user.set_password(password)
            user.save()
            messages.add_message(request, messages.SUCCESS, "your password changed successfully")
            return redirect("login")


class ContactList(BaseList):
    model = Contacts
    template_name = 'users/contact_list.html'

    def get_queryset(self):
        return Contacts.objects.filter(owner=self.request.user.pk)


class ContactDetail(LoginRequiredMixin, DetailView):
    model = Contacts
    template_name = 'users/contact_detail.html'
    context_object_name = 'contact'

    def get_context_data(self, **kwargs):
        context = super(ContactDetail, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context


@login_required(redirect_field_name='login')
def new_contact(request):
    if request.method == "POST":
        form = NewContact(request.POST)
        form.birth_date = request.POST.get("birth_date")
        try:
            if form.is_valid():
                contact = form.save(commit=False)
                contact.owner = User.objects.get(pk=request.user.pk)

                try:
                    user = User.objects.get(username=contact.email)
                except ObjectDoesNotExist:
                    messages.add_message(request, messages.ERROR, f"this email dose not exist in the site")
                    return redirect(request.META.get('HTTP_REFERER'))

                if user:
                    contact.save()
                    return redirect('contacts')
        except IntegrityError:
            messages.add_message(request, messages.ERROR, f"You saved this contact once")
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            messages.add_message(request, messages.ERROR, message=form.errors)
            return redirect(request.META.get('HTTP_REFERER'))


class UpdateContact(LoginRequiredMixin, UpdateView):
    model = Contacts
    context_object_name = 'contact'
    fields = ['name', 'email', 'birth_date', 'emails', 'phone']
    template_name = 'users/edit_contact.html'

    def get_success_url(self):
        self.success_url = f"/accounts/contact-detail/{self.object.pk}/"
        return self.success_url

    def get_context_data(self, **kwargs):
        context = super(UpdateContact, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        context['signatures'] = Signature.objects.filter(owner__id=self.request.user.pk)
        return context


@login_required(redirect_field_name='login')
def delete_contact(request, pk):
    if request.method == 'GET':
        contact = Contacts.objects.get(pk=pk)
        contact.delete()
        return redirect('contacts')


@login_required(redirect_field_name='login')
def email_contact(request, email):
    if request.method == "POST":
        sender = User.objects.get(pk=request.user.pk)
        form = NewEmailForm(request.POST, request.FILES)
        if request.POST.get('signature') != 'None':
            signature = Signature.objects.get(owner_id=sender.pk,
                                              text=request.POST.get('signature')).pk
        else:
            signature = None
        if 'email_submit' in request.POST:
            if form.is_valid():
                receiver = User.objects.get(username=email)
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=form.cleaned_data['text'],
                                              file=form.cleaned_data['file'],
                                              status='send',
                                              is_to=True,
                                              signature_id=signature
                                              )
                email.receiver.add(receiver)
                email.receiver_to.add(receiver)
                email.save()
                place = EmailPlace.objects.create(user=sender, email=email)
                place = EmailPlace.objects.create(user=receiver, email=email)

                return redirect('sent')
            messages.add_message(request, messages.ERROR, message=form.errors)
            return redirect(request.META.get('HTTP_REFERER'))

        if 'draft_submit' in request.POST:
            if form.is_valid() is False or form.is_valid() is True:
                creat_draft(form, sender, signature)
                return redirect('draft')


@login_required(redirect_field_name='login')
def csv_contacts(request):
    contacts = list(Contacts.objects.filter(owner=request.user.pk).values())
    response = HttpResponse()
    # to tell the http the format of the file in response
    response['Content-Disposition'] = f"attachment; filename={request.user.username}-contacts.csv"
    writer = csv.writer(response)
    # the headers we have
    writer.writerow(contacts[0].keys())
    for contact in contacts:
        writer.writerow(contact.values())

    return response


@login_required(redirect_field_name='login')
def search_contact(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        contacts = Contacts.objects.filter(
            Q(owner=request.user),
            Q(name__icontains=search_str) |
            Q(email__icontains=search_str) |
            Q(emails__icontains=search_str) |
            Q(phone__icontains=search_str)
        )
        data = contacts.values()
        return JsonResponse(list(data), safe=False)  # safe let to return a not json response
