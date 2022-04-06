import json

from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from emails.models import *


class EmailDetailViewsTest(TestCase):
    def setUp(self):
        # Create  user
        test_user1 = User.objects.create_user(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2@gmz.com', password='2HJ1vRV0Z&3iD')
        test_user1.save()
        test_user2.save()

        # Create signature
        test_signature1 = Signature.objects.create(owner=test_user1, text='test1')
        test_signature1.save()
        test_signature2 = Signature.objects.create(owner=test_user2, text='test2')
        test_signature2.save()

        # Create test emails and their places
        test_email1 = Emails.objects.create(sender=test_user1, title='test1', signature=test_signature1, status='send')
        test_email1.save()
        test_email1.receiver.add(test_user2)
        test_place1_0 = EmailPlace.objects.create(email=test_email1, user=test_user1)
        test_place1_1 = EmailPlace.objects.create(email=test_email1, user=test_user2)

        test_email2 = Emails.objects.create(sender=test_user2, title='test2', signature=test_signature2, status='send')
        test_email2.save()
        test_email2.receiver.add(test_user2)  # send email to itself
        test_place2_1 = EmailPlace.objects.create(email=test_email2, user=test_user2)

        # create category
        test_cat1 = Category.objects.create(owner=test_user1, title='test1')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('email_detail', kwargs={'pk': 2}))
        self.assertRedirects(response, '/accounts/login/?next=/gmz-email/email-detail/2')

    def test_view_access_logged_in_email_detail(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1@gmz.com')
        email = Emails.objects.get(Q(sender=login_user) | Q(receiver=login_user))
        response = self.client.get(reverse('email_detail', kwargs={'pk': email.pk}))
        self.assertEqual(response.status_code, 200)

    def test_view_archive_or_trash_email(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1@gmz.com')
        email = Emails.objects.get(Q(sender=login_user) | Q(receiver=login_user))
        # Test adding or removing from archive
        response = self.client.get(reverse('add_archive', kwargs={'pk': email.pk}))
        self.assertEqual(response.status_code, 302)
        # Test adding or removing from trash
        response = self.client.get(reverse('add_trash', kwargs={'pk': email.pk}))
        self.assertEqual(response.status_code, 302)

    def test_view_set_label_to_email(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1@gmz.com')
        email = Emails.objects.get(Q(sender=login_user) | Q(receiver=login_user))
        response = self.client.post(reverse('set_label', kwargs={'pk': email.pk}),
                                    {'title': 'test1'}, follow=True,
                                    HTTP_REFERER='/accounts/login/')
        message = list(response.context.get('messages'))[0]
        # Check if select a valid label
        self.assertEqual("Successfully added to label list!", message.message)
        # Check if select an invalid label
        response = self.client.post(reverse('set_label', kwargs={'pk': email.pk}),
                                    {'title': '...'}, follow=True,
                                    HTTP_REFERER='/accounts/login/')
        message = list(response.context.get('messages'))[0]
        self.assertEqual("Select a label title!", message.message)

    def test_view_reply_email(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1@gmz.com')
        email = Emails.objects.get(Q(sender=login_user) | Q(receiver=login_user))
        data = {
            'title': 'test11',
            'file': '',
            'text': 'test test',
            'signature': 'None',
            'email_submit': 'email_submit'
        }
        # Test reply successfully to an email
        response = self.client.post(reverse('reply_email', kwargs={'pk': email.pk}),
                                    data, follow=True, )
        self.assertRedirects(response, '/gmz-email/sent/')
        # Test draft successfully to an email
        data = {
            'title': 'test11',
            'file': '',
            'text': 'test test',
            'signature': 'None',
            'draft_submit': 'draft_submit'
        }
        response = self.client.post(reverse('reply_email', kwargs={'pk': email.pk}),
                                    data, follow=True, )
        self.assertRedirects(response, '/gmz-email/draft/')

    def test_view_forward_email(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1@gmz.com')
        email = Emails.objects.get(Q(sender=login_user) | Q(receiver=login_user))
        data = {
            'title': 'test forward',
            'receiver_to': 'testuser2@gmz.com',
            'receiver_cc': '',
            'receiver_bcc': '',
            'email_submit': 'email_submit'
        }
        # Test forward successfully to an email
        response = self.client.post(reverse('forward_email', kwargs={'pk': email.pk}),
                                    data, follow=True, )
        self.assertRedirects(response, '/gmz-email/sent/')
        # Test draft successfully of forward
        data = {
            'title': 'test forward',
            'receiver_to': 'testuser2@gmz.com',
            'receiver_cc': '',
            'receiver_bcc': '',
            'draft_submit': 'draft_submit'
        }
        response = self.client.post(reverse('forward_email', kwargs={'pk': email.pk}),
                                    data, follow=True, )
        self.assertRedirects(response, '/gmz-email/draft/')


class EmailListViewsTest(TestCase):
    def setUp(self):
        # Create  user
        test_user1 = User.objects.create_user(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2@gmz.com', password='2HJ1vRV0Z&3iD')
        test_user1.save()
        test_user2.save()

        # create category
        test_cat1 = Category.objects.create(owner=test_user1, title='test1')

    def test_view_create_new_email(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        data = {
            'title': 'test forward',
            'receiver_to': 'testuser2@gmz.com',
            'receiver_cc': '',
            'receiver_bcc': '',
            'signature': 'None',
            'file': '',
            'email_submit': 'email_submit'
        }
        # Test forward successfully to an email
        response = self.client.post(reverse('new_email'),
                                    data, follow=True, )
        self.assertRedirects(response, '/gmz-email/sent/')
        # Test draft successfully of forward
        data = {
            'title': 'test forward',
            'receiver_to': 'testuser2@gmz.com',
            'receiver_cc': '',
            'receiver_bcc': '',
            'signature': 'None',
            'file': '',
            'draft_submit': 'draft_submit'
        }
        response = self.client.post(reverse('new_email'),
                                    data, follow=True, )
        self.assertRedirects(response, '/gmz-email/draft/')

    def test_view_logged_in_user_search_emails(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        data = json.dumps({'searchText': 'test'})
        response = self.client.generic('POST', reverse('search_email'), data)
        self.assertEqual(response.status_code, 200)

    def test_view_creat_new_label(self):
        login = self.client.login(username='testuser1@gmz.com', password='1X<ISRUkw+tuK')
        # Test if it found the integrity error
        data = {'title': 'test1'}
        response = self.client.post(reverse('new_label'), data, follow=True,
                                    HTTP_REFERER='/accounts/login/')

        message = list(response.context.get('messages'))[0]
        self.assertEqual("The label exist", message.message)
        # Test if it create the label
        # data = {'title': 'test2'}
        # response = self.client.post(reverse('new_label'), data, follow=True,
        #                             HTTP_REFERER='/accounts/login/')
        # message = list(response.context.get('messages'))[0]
        # self.assertEqual("The label added successfully", message.message)