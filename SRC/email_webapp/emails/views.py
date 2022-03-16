import json
import mimetypes
import os
from time import strftime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import *
from .forms import *
from accounts.forms import NewContact
from accounts.models import *
from .extera_handeler import *


def find_filter_emails(request, emails):
    for email in emails:
        filters = FilterInfo.objects.filter(Q(username__username=email.sender) |
                                            Q(subject=email.title),
                                            owner=request.user,
                                            )
        if filters:
            for tag in filters:
                if tag.label is None:
                    if tag.is_archive is True:
                        label = 'archive'
                    elif tag.is_trash is True:
                        label = 'trash'
                else:
                    label = tag.label
                filter_email_status = FilterEmailStatus.objects.filter(email=email,
                                                                       label=label,
                                                                       filter_user_id=request.user.id
                                                                       )
                if not filter_email_status:
                    filter_email_status = FilterEmailStatus.objects.create(email=email,
                                                                           is_filter=True,
                                                                           active_label=True,
                                                                           label=label,
                                                                           filter_user_id=request.user.id
                                                                           )
                    if label == "trash":
                        places = EmailPlace.objects.filter(email=email.pk, user=request.user.pk)
                        for place in places:
                            place.is_trash = True
                            place.save()

                    elif label == "archive":
                        places = EmailPlace.objects.filter(email=email.pk, user=request.user.pk)
                        for place in places:
                            place.is_archive = True
                            place.save()

                    else:
                        cat = Category.objects.get(title=label,owner=request.user)
                        email.category.add(cat)

    return emails


class BaseList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'

    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"

    def get_context_data(self, **kwargs):
        context = super(BaseList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        context['form3'] = FilterForm()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        context['labels'] = Category.objects.filter(owner_id=self.request.user.pk)
        return context


class InboxList(BaseList):
    model = Emails
    template_name = 'emails/inbox_list.html'

    def get_queryset(self):
        emails = Emails.objects.filter(receiver=self.request.user.pk)
        emails = find_filter_emails(request=self.request, emails=emails)

        for email in emails:

            place = EmailPlace.objects.filter(email=email.pk, user=self.request.user.pk)
            for item in place:
                if item.is_trash or item.is_archive is True:
                    emails = emails.exclude(pk=email.pk)

        for email in emails:
            filter_email_status = FilterEmailStatus.objects.filter(email=email.pk)
            for status in filter_email_status:
                if status.active_label is True:
                    emails = emails.exclude(pk=email.pk)

        return emails


class SentList(BaseList):
    model = Emails
    context_object_name = 'emails'
    template_name = 'emails/sent_list.html'

    def get_queryset(self):
        emails = Emails.objects.filter(sender=self.request.user.pk, status="send")
        for email in emails:
            place = EmailPlace.objects.filter(email=email.pk, user=self.request.user.pk)
            for item in place:
                if item.is_trash is True or item.is_archive is True:
                    emails = emails.exclude(pk=email.pk)
        return emails


class DraftList(BaseList):
    model = Emails
    template_name = 'emails/draft_list.html'

    def get_queryset(self):
        emails = Emails.objects.filter(sender=self.request.user.pk, status="draft")
        for email in emails:
            place = EmailPlace.objects.filter(email=email.pk, user=self.request.user.pk)
            for item in place:
                if item.is_trash or item.is_archive is True:
                    emails = emails.exclude(pk=email.pk)
        return emails


class TrashList(BaseList):
    model = Emails
    template_name = 'emails/trash_list.html'

    def get_queryset(self):
        emails = Emails.objects.filter(Q(sender=self.request.user.pk) | Q(receiver=self.request.user.pk))
        for email in emails:
            place = EmailPlace.objects.filter(email=email.pk, user=self.request.user.pk)
            for item in place:
                if item.is_trash is False or item.is_archive is True:
                    emails = emails.exclude(pk=email.pk)
        return emails


class ArchiveList(BaseList):
    model = Emails
    template_name = 'emails/archive_list.html'

    def get_queryset(self):
        emails = Emails.objects.filter(Q(sender=self.request.user.pk) | Q(receiver=self.request.user.pk))
        for email in emails:
            place = EmailPlace.objects.filter(email=email.pk, user=self.request.user.pk)
            for item in place:
                if item.is_trash is True or item.is_archive is False:
                    emails = emails.exclude(pk=email.pk)
        return emails


@login_required(redirect_field_name='login')
def new_email(request):
    if request.method == "POST":
        sender = User.objects.get(pk=request.user.pk)
        form = NewEmailForm(request.POST, request.FILES)
        if request.POST.get('signature') != 'None':
            signature = Signature.objects.get(owner_id=sender.pk,
                                              text=request.POST.get('signature')).pk
        else:
            signature = None
        if 'email_submit' in request.POST:
            receivers_to, receivers_bcc, receivers_cc, receivers = [], [], [], []
            is_to, is_bcc, is_cc = False, False, False
            if request.POST.get('receiver_to'):
                receivers = request.POST.get('receiver_to').split(',')
                receivers_to = request.POST.get('receiver_to').split(',')
                is_to = True
            if request.POST.get('receiver_cc'):
                receivers = receivers + request.POST.get('receiver_cc').split(',')
                receivers_cc = request.POST.get('receiver_cc').split(',')
                is_cc = True
            if request.POST.get('receiver_bcc'):
                receivers = receivers + request.POST.get('receiver_bcc').split(',')
                receivers_bcc = request.POST.get('receiver_bcc').split(',')
                is_bcc = True

            # to find the objects with queryset
            users_to = User.objects.filter(username__in=receivers_to)
            users_cc = User.objects.filter(username__in=receivers_cc)
            users_bcc = User.objects.filter(username__in=receivers_bcc)
            users = User.objects.filter(username__in=receivers)

            # if there is not any valid registered user within inputs
            if len(users) == 0:
                messages.add_message(request, messages.ERROR, f"There most be at least one valid username!")
                return redirect(request.META.get('HTTP_REFERER'))
            # to check the valid inputs
            for user in users:
                while user.username in receivers:
                    receivers.remove(user.username)
            # to return invalid username inputs
            if len(receivers) > 0:
                for receiver in receivers:
                    messages.add_message(request, messages.ERROR,
                                         f"user with {receiver} username dose not exist!")
                    return redirect(request.META.get('HTTP_REFERER'))

            if form.is_valid():
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=form.cleaned_data['text'],
                                              file=form.cleaned_data['file'],
                                              status='send',
                                              is_bcc=is_bcc,
                                              is_cc=is_cc,
                                              is_to=is_to,
                                              signature_id=signature
                                              )
                email.receiver.add(*users)
                email.receiver_cc.add(*users_cc)
                email.receiver_bcc.add(*users_bcc)
                email.receiver_to.add(*users_to)
                for user in users:
                    place = EmailPlace.objects.create(user=user, email=email)
                place = EmailPlace.objects.create(user=sender, email=email)

                messages.add_message(request, messages.SUCCESS, f"Successfully sent !")
                return redirect('sent')

            messages.add_message(request, messages.ERROR,
                                 message=form.errors)
            return redirect(request.META.get('HTTP_REFERER'))

        if 'draft_submit' in request.POST:
            form = NewEmailForm(request.POST, request.FILES)
            if form.is_valid() is False or form.is_valid() is True:
                creat_draft(form, sender, signature)
                messages.add_message(request, messages.SUCCESS, f"Draft email! ")
                return redirect('draft')


class EmailDetail(LoginRequiredMixin, DetailView):
    model = Emails
    template_name = 'emails/email_detail.html'
    context_object_name = 'email'

    def get_context_data(self, **kwargs):
        context = super(EmailDetail, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        context['labels'] = Category.objects.filter(owner_id=self.request.user.pk)

        if context['email'].category:
            context['email_labels'] = list(
                context['email'].category.filter(owner_id=self.request.user.pk).values_list('title', flat=True))

        if context['email'].reply_to:
            email_parent = Emails.objects.get(pk=context['email'].reply_to.pk)
            context['parent_text'] = email_parent.text
            context['parent_sender'] = email_parent.sender

        places = EmailPlace.objects.filter(email=self.object, user=self.request.user.pk)
        for place in places:
            if place.is_trash is True:
                context['trash'] = True
            else:
                context['trash'] = False

        if context['email'].status == 'draft':
            # because draft emails were saved without receivers
            return context

        # check if the email receiver is a to, cc or bcc type
        url = self.request.META.get('HTTP_REFERER').split('/')

        receivers_to = list(context.get('email').receiver_to.filter().values_list('username', flat=True))
        receivers_cc = list(context.get('email').receiver_cc.filter().values_list('username', flat=True))
        receivers_bcc = list(context.get('email').receiver_bcc.filter().values_list('username', flat=True))

        if "sent" in url:
            context['people'] = list(context.get('email').receiver.filter().values_list('username', flat=True))
            return context

        if context['email'].is_to or context['email'].is_bcc is True:
            if self.request.user.username in receivers_bcc or \
                    self.request.user.username in receivers_to:
                context['person'] = self.request.user
                return context

        if context['email'].is_cc is True:
            if self.request.user.username in receivers_cc:
                context['people'] = list(
                    context.get('email').receiver_cc.filter().values_list('username', flat=True))
                return context


@login_required(redirect_field_name='login')
def check_archive(request, pk):
    if request.method == "GET":
        email = Emails.objects.get(pk=pk)
        places = EmailPlace.objects.filter(user=request.user.pk, email=email.pk)

        for place in places:
            if place.is_archive is False:
                place.is_archive = True
            elif place.is_archive is True:
                place.is_archive = False
            place.save(update_fields=['is_archive'])

        find_filter_labels = FilterEmailStatus.objects.filter(email=email.pk, label='archive')
        if find_filter_labels:
            for item in find_filter_labels:
                item.active_label = False
                item.save()

        return redirect('archive')


@login_required(redirect_field_name='login')
def check_trash(request, pk):
    if request.method == "GET":
        email = Emails.objects.get(pk=pk)
        places = EmailPlace.objects.filter(user=request.user.pk, email=email.pk)
        for place in places:
            if place.is_trash is False:
                place.is_trash = True
                print(place)
            elif place.is_trash is True:
                place.is_trash = False
                print(place)
            place.save(update_fields=['is_trash'])

        find_filter_labels = FilterEmailStatus.objects.filter(email=email.pk, label='trash')
        if find_filter_labels:
            for item in find_filter_labels:
                item.active_label = False
                item.save()

        return redirect('trash')


class LabelEmailList(BaseList):
    model = Emails
    template_name = 'emails/label_email_list.html'

    def get_queryset(self):
        # the pk is the pk pg the category
        pk = self.kwargs['pk']
        emails = Emails.objects.filter(category__id=pk, receiver=self.request.user.pk)
        filters = Emails.objects.filter(receiver=self.request.user.pk)

        for email in emails:
            place = EmailPlace.objects.filter(email=email.pk, user=self.request.user.pk)
            for item in place:
                if item.is_trash is True or item.is_archive is True:
                    emails = emails.exclude(pk=email.pk)

        return emails


@login_required(redirect_field_name='login')
def new_label(request):
    if request.method == "POST":
        title = request.POST.get('title')
        owner = request.user.pk
        try:
            new_cat = Category(owner_id=owner,
                               title=title)
            new_cat.save()
            messages.add_message(request, messages.SUCCESS, "The label added successfully")

            return redirect(request.META.get('HTTP_REFERER'))
        except IntegrityError:
            messages.add_message(request, messages.SUCCESS, "The label exist")
            return redirect(request.META.get('HTTP_REFERER'))


@login_required(redirect_field_name='login')
def delete_label(request):
    if request.method == "POST":
        title = request.POST.get('title')
        owner = request.user.pk
        if title == "...":
            messages.add_message(request, messages.SUCCESS, "Select a label title!")
            return redirect('inbox')

        cat = Category.objects.get(owner_id=owner, title=title)
        cat.delete()
        messages.add_message(request, messages.SUCCESS, "The label deleted successfully")
        return redirect('inbox')


@login_required(redirect_field_name='login')
def reply_email(request, pk):
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
                reply_to = Emails.objects.get(pk=pk)
                receiver_to = User.objects.get(username=reply_to.sender)
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=form.cleaned_data['text'],
                                              file=form.cleaned_data['file'],
                                              status='send',
                                              is_to=True,
                                              reply_to=reply_to,
                                              signature_id=signature
                                              )

                email.receiver.add(receiver_to)
                email.receiver_to.add(receiver_to)
                email.save()

                place = EmailPlace.objects.create(user=sender, email=email)
                place = EmailPlace.objects.create(user=receiver_to, email=email)
                return redirect('sent')
            return render(request, 'emails/new_error.html', {'form': form})

        if 'draft_submit' in request.POST:
            if form.is_valid() is False or form.is_valid() is True:
                creat_draft(form, sender, signature)
                return redirect('draft')


@login_required(redirect_field_name='login')
def set_label(request, pk):
    if request.method == "POST":
        email = Emails.objects.get(pk=pk)
        title = request.POST.get("title")
        owner = request.user.pk
        if title == "...":
            messages.add_message(request, messages.SUCCESS, "Select a label title!")
            return redirect(request.META.get('HTTP_REFERER'))
        cat = Category.objects.get(owner_id=owner, title=title)
        email.category.add(cat.pk)
        messages.add_message(request, messages.SUCCESS, "Successfully added to label list!")
        return redirect(request.META.get('HTTP_REFERER'))


@login_required(redirect_field_name='login')
def remove_from_label(request, pk):
    if request.method == "POST":
        email = Emails.objects.get(pk=pk)
        title = request.POST.get("title")
        owner = request.user.pk
        if title == "...":
            messages.add_message(request, messages.SUCCESS, "Select a label title!")
            return redirect(request.META.get('HTTP_REFERER'))
        cat = Category.objects.get(owner_id=owner, title=title)
        email.category.remove(cat.pk)

        find_filter_labels = FilterEmailStatus.objects.filter(email=email.pk, label=title)
        if find_filter_labels:
            for item in find_filter_labels:
                item.active_label = False
                item.save()

        messages.add_message(request, messages.SUCCESS, "Successfully removed from label list!")
        return redirect(request.META.get('HTTP_REFERER'))


@login_required(redirect_field_name='login')
def download_file(request, filename):
    # Define Django project base directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Define the full file path
    filepath = BASE_DIR + '/uploads/' + filename
    # Open the file for reading content
    path = open(filepath, 'rb')
    # Set the mime type
    mime_type, _ = mimetypes.guess_type(filepath)
    # Set the return value of the HttpResponse
    response = HttpResponse(path, content_type=mime_type)
    # Set the HTTP header for sending to browser
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    # Return the response value
    return response


@login_required(redirect_field_name='login')
def forward_email(request, pk):
    if request.method == "POST":
        sender = User.objects.get(pk=request.user.pk)
        from_email = Emails.objects.get(pk=pk)
        form = NewEmailForm(request.POST)

        if 'email_submit' in request.POST:
            is_to, is_bcc, is_cc = False, False, False
            receivers_to, receivers_bcc, receivers_cc, receivers = [], [], [], []

            if request.POST.get('receiver_to'):
                receivers = request.POST.get('receiver_to').split(',')
                receivers_to = request.POST.get('receiver_to').split(',')
                is_to = True

            if request.POST.get('receiver_cc'):
                receivers = receivers + request.POST.get('receiver_cc').split(',')
                receivers_cc = request.POST.get('receiver_cc').split(',')
                is_cc = True

            if request.POST.get('receiver_bcc'):
                receivers = receivers + request.POST.get('receiver_bcc').split(',')
                receivers_bcc = request.POST.get('receiver_bcc').split(',')
                is_bcc = True

            users_to = User.objects.filter(username__in=receivers_to)
            users_cc = User.objects.filter(username__in=receivers_cc)
            users_bcc = User.objects.filter(username__in=receivers_bcc)
            users = User.objects.filter(username__in=receivers)

            if len(users) == 0:
                messages.add_message(request, messages.ERROR, f"There most be at least one valid username!")
                return redirect(request.META.get('HTTP_REFERER'))

            for user in users:
                while user.username in receivers:
                    receivers.remove(user.username)

            if len(receivers) > 0:
                for receiver in receivers:
                    messages.add_message(request, messages.ERROR,
                                         f"user with {receiver} username dose not exist!")
                    return redirect(request.META.get('HTTP_REFERER'))

            if form.is_valid():
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=from_email.text,
                                              file=from_email.file,
                                              status='send',
                                              is_bcc=is_bcc,
                                              is_cc=is_cc,
                                              is_to=is_to,
                                              signature_id=from_email.signature
                                              )
                email.receiver.add(*users)
                email.receiver_cc.add(*users_cc)
                email.receiver_bcc.add(*users_bcc)
                email.receiver_to.add(*users_to)

                for user in users:
                    place = EmailPlace.objects.create(user=user, email=email)

                place = EmailPlace.objects.create(user=sender, email=email)

                messages.add_message(request, messages.SUCCESS, f"Successfully sent !")
                return redirect('sent')
            messages.add_message(request, messages.ERROR,
                                 message=form.errors)
            return redirect(request.META.get('HTTP_REFERER'))

        if 'draft_submit' in request.POST:
            if form.is_valid() is False or form.is_valid() is True:
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=from_email.text,
                                              file=from_email.file,
                                              status='draft',
                                              signature_id=from_email.signature
                                              )
                email.save()
                place = EmailPlace.objects.create(user=sender, email=email)
                place.save()
                messages.add_message(request, messages.SUCCESS, f"Draft email! ")
                return redirect('draft')


@login_required(redirect_field_name='login')
def edit_draft(request, pk):
    if request.method == "POST":
        sender = User.objects.get(pk=request.user.pk)
        form = NewEmailForm(request.POST, request.FILES)
        email = Emails.objects.get(pk=pk)
        if request.POST.get('signature') != 'None':
            signature = Signature.objects.get(owner_id=sender.pk,
                                              text=request.POST.get('signature')).pk
        else:
            signature = None
        if 'email_submit' in request.POST:
            receivers_to, receivers_bcc, receivers_cc, receivers = [], [], [], []
            is_to, is_bcc, is_cc = False, False, False
            if request.POST.get('receiver_to'):
                receivers = request.POST.get('receiver_to').split(',')
                receivers_to = request.POST.get('receiver_to').split(',')
                is_to = True
            if request.POST.get('receiver_cc'):
                receivers = receivers + request.POST.get('receiver_cc').split(',')
                receivers_cc = request.POST.get('receiver_cc').split(',')
                is_cc = True
            if request.POST.get('receiver_bcc'):
                receivers = receivers + request.POST.get('receiver_bcc').split(',')
                receivers_bcc = request.POST.get('receiver_bcc').split(',')
                is_bcc = True

            # to find the objects with queryset
            users_to = User.objects.filter(username__in=receivers_to)
            users_cc = User.objects.filter(username__in=receivers_cc)
            users_bcc = User.objects.filter(username__in=receivers_bcc)
            users = User.objects.filter(username__in=receivers)

            # if there is not any valid registered user within inputs
            if len(users) == 0:
                messages.add_message(request, messages.ERROR, f"There most be at least one valid username!")
                return redirect(request.META.get('HTTP_REFERER'))
            # to check the valid inputs
            for user in users:
                while user.username in receivers:
                    receivers.remove(user.username)
            # to return invalid username inputs
            if len(receivers) > 0:
                for receiver in receivers:
                    messages.add_message(request, messages.ERROR,
                                         f"user with {receiver} username dose not exist!")
                    return redirect(request.META.get('HTTP_REFERER'))

            if form.is_valid():
                email.title = form.cleaned_data['title']
                email.text = form.cleaned_data['text']
                email.file = form.cleaned_data['file']
                email.status = 'send'
                email.is_bcc = is_bcc
                email.is_cc = is_cc
                email.is_to = is_to
                email.signature_id = signature
                email.receiver.add(*users)
                email.receiver_cc.add(*users_cc)
                email.receiver_bcc.add(*users_bcc)
                email.receiver_to.add(*users_to)

                for user in users:
                    place = EmailPlace.objects.create(user=user, email=email)

                place = EmailPlace.objects.create(user=sender, email=email)

                messages.add_message(request, messages.ERROR,
                                     message=form.errors)
                return redirect(request.META.get('HTTP_REFERER'))

            messages.add_message(request, messages.ERROR,
                                 message=form.errors)
            return redirect(request.META.get('HTTP_REFERER'))

        if 'draft_submit' in request.POST:
            form = NewEmailForm(request.POST, request.FILES)
            if form.is_valid() is False or form.is_valid() is True:
                email.title = form.cleaned_data['title']
                email.text = form.cleaned_data['text']
                email.file = form.cleaned_data['file']
                email.status = 'draft'
                email.save()
                place = EmailPlace.objects.create(user=sender, email=email)
                place.save()
                messages.add_message(request, messages.SUCCESS, f"Draft email! ")
                return redirect('draft')


@login_required(redirect_field_name='login')
def new_signature(request):
    if request.method == "POST":
        text = request.POST.get('text')
        owner = request.user.pk
        new_sign = Signature.objects.create(owner_id=owner,
                                            text=text)
        messages.add_message(request, messages.SUCCESS, "The signature added successfully")

        return redirect(request.META.get('HTTP_REFERER'))


@login_required(redirect_field_name='login')
def delete_signature(request):
    if request.method == "POST":
        text = request.POST.get('text')
        owner = request.user.pk
        if text == "...":
            messages.add_message(request, messages.SUCCESS, "Select a sign text!")
            return redirect('inbox')

        try:
            sign = Signature.objects.get(owner_id=owner, text=text)
            sign.delete()
        except Exception as e:
            raise e
        messages.add_message(request, messages.SUCCESS, "The sign deleted successfully")
        return redirect('inbox')


@login_required(redirect_field_name='login')
def search_email(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        emails = Emails.objects.filter(
            Q(sender=request.user.pk) | Q(receiver=request.user.pk),
            Q(title__icontains=search_str) |
            Q(text__icontains=search_str) |
            Q(emails__category__title=search_str) |
            Q(pub_date__istartswith=search_str) |
            Q(receiver__username__icontains=search_str) |
            Q(emails__sender__username__icontains=search_str)
        )
        data = emails.values()
        for email in data:
            email['sender_id'] = User.objects.get(pk=email['sender_id']).username
            email['pub_date'] = email['pub_date'].date()
        print(data)
        return JsonResponse(list(data), safe=False)  # safe let to return a not json response


@login_required(redirect_field_name='login')
def new_filter(request):
    if request.method == "POST":
        form = FilterForm(request.POST)

        if request.POST.get('label') == '...':
            messages.add_message(request, messages.ERROR,
                                 message="You must select a label")
            return redirect(request.META.get('HTTP_REFERER'))

        if request.POST.get('username'):
            if form.is_valid() is False:
                messages.add_message(request, messages.ERROR,
                                     message=form.errors)
                return redirect(request.META.get('HTTP_REFERER'))

            username = User.objects.get(username=form.cleaned_data['username'])

            if username:
                pass
            else:
                messages.add_message(request, messages.ERROR,
                                     message="username dose not exist")
                return redirect(request.META.get('HTTP_REFERER'))

        else:
            username = None

        if form.is_valid():
            if request.POST.get('label') != "trash":
                cat = Category.objects.get(title=request.POST.get('label'),owner=request.user)
                is_trash = False
                is_archive = False
            else:
                cat = None
                is_trash = True
                is_archive = False

            new_filter = FilterInfo.objects.create(
                owner=request.user,
                username=username,
                subject=form.cleaned_data['subject'],
                label=cat,
                is_trash=is_trash,
                is_archive=is_archive
            )

            messages.add_message(request, messages.ERROR,
                                 message="Filter added successfully")
            return redirect(request.META.get('HTTP_REFERER'))
