from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import *
from .forms import *
from emails.models import Emails
from accounts.forms import NewContact
from accounts.models import *


class InboxList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"
    model = Emails
    template_name = 'emails/inbox_list.html'

    def get_context_data(self, **kwargs):
        context = super(InboxList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    def get_queryset(self):
        return Emails.objects.filter(~Q(status="trash"),
                                     receiver=self.request.user.pk,
                                     is_archive=False,
                                     )


class SentList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"
    model = Emails
    context_object_name = 'emails'
    template_name = 'emails/sent_list.html'

    def get_context_data(self, **kwargs):
        context = super(SentList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    def get_queryset(self):
        return Emails.objects.filter(~Q(status="trash"),
                                     sender=self.request.user.pk,
                                     status="send",
                                     is_archive=False)


class DraftList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"
    model = Emails
    template_name = 'emails/draft_list.html'

    def get_context_data(self, **kwargs):
        context = super(DraftList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    def get_queryset(self):
        return Emails.objects.filter(~Q(status="trash"),
                                     sender=self.request.user.pk,
                                     status="draft",
                                     is_archive=False)


class TrashList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"
    model = Emails
    template_name = 'emails/trash_list.html'

    def get_context_data(self, **kwargs):
        context = super(TrashList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    def get_queryset(self):
        return Emails.objects.filter(
            Q(sender=self.request.user.pk) | Q(receiver=self.request.user.pk),
            status="trash")


class ArchiveList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"
    model = Emails
    template_name = 'emails/archive_list.html'

    def get_context_data(self, **kwargs):
        context = super(ArchiveList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    def get_queryset(self):
        return Emails.objects.filter(
            ~Q(status="trash"),
            Q(sender=self.request.user.pk) | Q(receiver=self.request.user.pk),
            is_archive=True)


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
            receivers = []
            is_to, is_bcc, is_cc = False, False, False
            if request.POST.get('receiver_to'):
                receivers.append(request.POST.get('receiver_to'))
                is_to = True
            if request.POST.get('receiver_cc'):
                receivers = receivers + request.POST.get('receiver_cc').split(',')
                is_cc = True
            if request.POST.get('receiver_bcc'):
                receivers = receivers + request.POST.get('receiver_bcc').split(',')
                is_bcc = True
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
                                              text=form.cleaned_data['text'],
                                              file=form.cleaned_data['file'],
                                              status='send',
                                              is_bcc=is_bcc,
                                              is_cc=is_cc,
                                              is_to=is_to,
                                              signature_id=signature
                                              )
                for user in users:
                    email.receiver.add(user)
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
        url = self.request.META.get('HTTP_REFERER').split('/')
        if "inbox" in url or "trash" in url:
            if context['email'].is_to or context['email'].is_bcc is True:
                context['person'] = self.request.user
            if context['email'].is_cc is True:
                context['people'] = list(context.get('email').receiver.filter().values_list('username', flat=True))
            return context
        context['people'] = list(context.get('email').receiver.filter().values_list('username', flat=True))
        return context


@login_required(redirect_field_name='login')
def add_archive(request, pk):
    if request.method == "GET":
        email = Emails.objects.get(pk=pk)
        email.is_archive = True
        email.save()
        return redirect('archive')


@login_required(redirect_field_name='login')
def add_trash(request, pk):
    if request.method == "GET":
        email = Emails.objects.get(pk=pk)
        email.status = 'trash'
        email.save()
        return redirect('trash')
