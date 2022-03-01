from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import *
from django.views.generic.edit import FormMixin
from .forms import *
from emails.models import Emails
from accounts.models import *
from django.http import HttpResponse, HttpResponseRedirect


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
        return Emails.objects.filter(receiver=self.request.user.pk)


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
        context['receivers'] = User.objects.filter(pk__in=list(context['emails'].values_list('receiver', flat=True)))
        return context

    def get_queryset(self):
        return Emails.objects.filter(sender=self.request.user.pk, status="send")


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
        return Emails.objects.filter(sender=self.request.user.pk, status="draft")


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
        return Emails.objects.filter(sender=self.request.user.pk, status="trash")


class ContactList(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # todo: set  permission_denied_message
    # permission_denied_message = "Login First"
    model = Contacts
    template_name = 'emails/contact_list.html'

    def get_context_data(self, **kwargs):
        context = super(ContactList, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    def get_queryset(self):
        return Contacts.objects.filter(owner=self.request.user.pk)


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
                form.add_error('receiver_to', 'There most be at least one receiver!')
                return render(request, 'emails/new_error.html', {'form': form})
            for user in users:
                while user.username in receivers:
                    receivers.remove(user.username)
                    print(receivers)
            print(receivers)
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


@login_required(redirect_field_name='login')
def new_contact(request):
    if request.method == "POST":
        form = NewContact(request.POST)
        try:
            if form.is_valid():
                contact = form.save(commit=False)
                contact.owner = User.objects.get(pk=request.user.pk)
                contact.birth_date = request.POST.get("birth_date")
                try:
                    user = User.objects.get(username=contact.email)
                except ObjectDoesNotExist:
                    form.add_error('email', "this email dose not exist in the site")
                    return render(request, 'emails/new_error.html', {'form': form})

                if user:
                    contact.save()
                    return redirect('contacts')
        except IntegrityError:
            form.add_error('email', "You saved this contact once")
            return render(request, 'emails/new_error.html', {'form': form})
        else:
            return render(request, 'emails/new_error.html', {'form': form})


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
        receivers = list(context.get('email').receiver.all())
        if self.request.user in receivers:
            if context['email'].is_to or context['email'].is_bcc is True:
                context['person'] = self.request.user
            if context['email'].is_cc is True:
                context['people'] = list(context.get('email').receiver.filter().values_list('username', flat=True))
        else:
            context['people'] = list(context.get('email').receiver.filter().values_list('username', flat=True))
        return context


class ContactDetail(LoginRequiredMixin, DetailView):
    model = Contacts
    template_name = 'emails/contact_detail.html'
    context_object_name = 'contact'

    def get_context_data(self, **kwargs):
        context = super(ContactDetail, self).get_context_data(**kwargs)
        context['form1'] = NewEmailForm()
        context['form2'] = NewContact()
        signatures = Signature.objects.filter(owner__id=self.request.user.pk)
        context['signatures'] = signatures
        return context

    # def post(self, request, pk):
    #     contact = get_object_or_404(Contacts, pk=pk)
    #     form = NewContact(request.POST)
    #     print(form.data)
    #     if form.is_valid():
    #         #     # from here you need to change your post request according to your requirement, this is just a demo
    #         obj = form.save(commit=False)
    #         contact.name = obj.name
    #         contact.email = obj.email
    #         contact.emails = obj.emails
    #         contact.phone = obj.phone
    #         contact.birth_date = obj.birth_date
    #         contact.save()
    #         return redirect('contact_detail', contact.id)
