import mimetypes
import os
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import *
from .forms import *
from emails.models import Emails
from accounts.forms import NewContact
from accounts.models import *


class BaseList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'

    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"

    def get_context_data(self, **kwargs):
        context = super(BaseList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        context['labels'] = Category.objects.filter(owner_id=self.request.user.pk)
        return context


class InboxList(BaseList):
    model = Emails
    template_name = 'emails/inbox_list.html'

    def get_queryset(self):
        return Emails.objects.filter(
            receiver=self.request.user.pk,
            is_archive=False,
            is_trash=False)


class SentList(BaseList):
    model = Emails
    context_object_name = 'emails'
    template_name = 'emails/sent_list.html'

    def get_queryset(self):
        return Emails.objects.filter(
            sender=self.request.user.pk,
            status="send",
            is_archive=False,
            is_trash=False)


class DraftList(BaseList):
    model = Emails
    template_name = 'emails/draft_list.html'

    def get_queryset(self):
        return Emails.objects.filter(
            sender=self.request.user.pk,
            status="draft",
            is_archive=False,
            is_trash=False)


class TrashList(BaseList):
    model = Emails
    template_name = 'emails/trash_list.html'

    def get_queryset(self):
        return Emails.objects.filter(
            Q(sender=self.request.user.pk) | Q(receiver=self.request.user.pk),
            is_trash=True)


class ArchiveList(BaseList):
    model = Emails
    template_name = 'emails/archive_list.html'

    def get_queryset(self):
        return Emails.objects.filter(
            Q(sender=self.request.user.pk) | Q(receiver=self.request.user.pk),
            is_archive=True, is_trash=False)


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
                form.add_error('receiver_to', 'There most be at least one valid receiver!')
                return render(request, 'emails/new_error.html', {'form': form})
            # to check the valid inputs
            for user in users:
                while user.username in receivers:
                    receivers.remove(user.username)
            # to return invalid username inputs
            if len(receivers) > 0:
                for receiver in receivers:
                    message = f"user with {receiver} username dose not exist!"
                    return render(request, 'emails/new_error.html', {'message': message})

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
                email.receiver_cc.add(*users)
                email.receiver.add(*users_cc)
                email.receiver.add(*users_bcc)
                email.receiver.add(*users_to)
                email.save()
                return redirect('sent')
            return render(request, 'emails/new_error.html', {'form': form})
        if 'draft_submit' in request.POST:
            if form.is_valid() is False or form.is_valid() is True:
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=form.cleaned_data['text'],
                                              file=form.cleaned_data['file'],
                                              status='draft',
                                              signature_id=signature
                                              )
                email.save()
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
            context['email_labels'] = list(context.get('email').category.filter().values_list('title', flat=True))

        if context['email'].reply_to:
            email_parent = Emails.objects.get(pk=context['email'].reply_to.pk)
            context['parent_text'] = email_parent.text
            context['parent_sender'] = email_parent.sender
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
                context['people'] = list(context.get('email').receiver_cc.filter().values_list('username', flat=True))
                return context


@login_required(redirect_field_name='login')
def check_archive(request, pk):
    if request.method == "GET":
        email = Emails.objects.get(pk=pk)
        if email.is_archive is False:
            email.is_archive = True
        elif email.is_archive is True:
            email.is_archive = False
        email.save(update_fields=['is_archive'])
        return redirect('archive')


@login_required(redirect_field_name='login')
def check_trash(request, pk):
    if request.method == "GET":
        email = Emails.objects.get(pk=pk)
        if email.is_trash is False:
            email.is_trash = True
        elif email.is_trash is True:
            email.is_trash = False
        email.save(update_fields=['is_trash'])
        return redirect('trash')


class LabelEmailList(BaseList):
    model = Emails
    template_name = 'emails/label_email_list.html'

    def get_queryset(self):
        # the pk is the pk pg the category
        pk = self.kwargs['pk']
        return Emails.objects.filter(category__id=pk,
                                     receiver=self.request.user.pk,
                                     is_archive=False,
                                     is_trash=False, )


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
                return redirect('sent')
            return render(request, 'emails/new_error.html', {'form': form})

        if 'draft_submit' in request.POST:
            if form.is_valid() is False or form.is_valid() is True:
                email = Emails.objects.create(sender=sender,
                                              title=form.cleaned_data['title'],
                                              text=form.cleaned_data['text'],
                                              file=form.cleaned_data['file'],
                                              status='draft',
                                              signature_id=signature
                                              )
                email.save()
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
                form.add_error('receiver_to', 'There most be at least one valid receiver!')
                return render(request, 'emails/new_error.html', {'form': form})

            for user in users:
                while user.username in receivers:
                    receivers.remove(user.username)

            if len(receivers) > 0:
                for receiver in receivers:
                    message = f"user with {receiver} username dose not exist!"
                    return render(request, 'emails/new_error.html', {'message': message})

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
                email.receiver_cc.add(*users)
                email.receiver.add(*users_cc)
                email.receiver.add(*users_bcc)
                email.receiver.add(*users_to)
                email.save()
                return redirect('sent')
            return render(request, 'emails/new_error.html', {'form': form})

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
                return redirect('draft')
