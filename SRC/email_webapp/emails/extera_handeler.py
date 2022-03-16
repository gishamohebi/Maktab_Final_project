from .models import Emails, EmailPlace


def creat_draft(form, sender, signature):
    email = Emails.objects.create(sender=sender,
                                  title=form.cleaned_data['title'],
                                  text=form.cleaned_data['text'],
                                  file=form.cleaned_data['file'],
                                  status='draft',
                                  signature_id=signature
                                  )
    place = EmailPlace.objects.create(user=sender, email=email)


# for email in emails:
#     # receiver = list(email.receiver.filter().values_list('username', flat=True))
#     filters = FilterInfo.objects.filter(Q(username__username=email.sender) |
#                                         Q(subject=email.title),
#                                         owner=self.request.user
#                                         )
#     if filters:
#         for filter in filters:
#             cat = Category.objects.get(title=filter.label)
#         email.category.add(cat)
#         email.save()
#         emails = emails.exclude(pk=email.pk)

# emails = Emails.objects.filter(receiver=self.request.user.pk)



