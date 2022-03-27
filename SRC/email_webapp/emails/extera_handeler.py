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



