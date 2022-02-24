from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
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
from .tokens import account_activation_token
from utils import send_otp_code, send_recover_link
from .forms import *
import random


def home(request):
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
        if form.is_valid():

            try:
                user = form.save(commit=False)  # Do not save to table yet
                user.username += "@gmz.com"
                validate_password(form.cleaned_data['password'], user)
            except ValidationError as e:
                form.add_error('password', e)  # to be displayed with the field's errors
                return render(request, "users/register_form.html", {'form': form})
            # except IntegrityError:
            #     form.add_error('username', "This username exist")
            #     return render(request, "users/register_form.html", {"form": form})

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

        return render(request, "users/register_form.html", {"form": form})


class Login(View):
    def get(self, request):
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
                    return redirect("login")
            login(request, user)
            return HttpResponse(f"Log in ! Wellcome ")

        messages.add_message(
            request, messages.ERROR,
            'wrong username or password')
        return redirect("login")


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
                else:
                    send_recovery_link(request, user)
                    message = "We sent your phone the recover link please check."
        except ObjectDoesNotExist:
            message = "This username dose not exist."
            messages.add_message(request, messages.INFO, message=message)
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
