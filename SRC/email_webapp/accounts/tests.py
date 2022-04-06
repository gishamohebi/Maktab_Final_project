import json
from django.test import TestCase
from django.urls import reverse
from emails.models import *


class ContactViewsTest(TestCase):

    def setUp(self):
        # Create  user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')
        test_user1.save()
        test_user2.save()

        # Create contact instance
        test_contact1 = Contacts.objects.create(owner=test_user1, name='gholi1', email='gholi1@gmz.com')
        test_contact2 = Contacts.objects.create(owner=test_user2, name='gholi2', email='gholi2@gmz.com')
        test_contact1.save()
        test_contact2.save()

        # Create signature
        test_signature1 = Signature.objects.create(owner=test_user1, text='test1')
        test_signature1.save()

    def test_view_urls_related_to_contacts_exists(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1')
        contact = Contacts.objects.get(owner=login_user.pk)
        # exists with url
        response = self.client.get('/accounts/contacts/')
        self.assertEqual(response.status_code, 200)
        # exists with name
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('detail_contact', kwargs={'pk': contact.pk}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('edit_contact', kwargs={'pk': contact.pk}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('delete_contact', kwargs={'pk': contact.pk}))
        self.assertEqual(response.status_code, 302)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('contacts'))
        self.assertRedirects(response, '/accounts/login/?next=/accounts/contacts/')

    def test_view_works_for_logged_in_user(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('contacts'))
        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)
        # Check we used correct template
        self.assertTemplateUsed(response, 'users/contact_list.html')

    def test_view_redirect_to_contact_detail_of_the_logged_in_user(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1')
        contact = Contacts.objects.get(owner=login_user.pk)
        # test if it redirect to the detail view of the log in user
        response = self.client.get(reverse('detail_contact', kwargs={'pk': contact.pk}))
        self.assertEqual(response.status_code, 200)
        # test if it raise 404 error when the contact dose not exist
        response = self.client.get(reverse('detail_contact', kwargs={'pk': 20}))
        self.assertEqual(response.status_code, 404)

    def test_view_logged_in_user_update_its_contact(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1')
        contact = Contacts.objects.get(owner=login_user.pk)
        response = self.client.get(reverse('edit_contact', kwargs={'pk': contact.pk}))
        # Check we used correct template
        self.assertTemplateUsed(response, 'users/edit_contact.html')
        response = self.client.post(reverse('edit_contact', kwargs={'pk': contact.pk}))
        # Check that we got a response "ok"
        self.assertEqual(response.status_code, 200)

    def test_view_logged_in_user_delete_its_contact(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        login_user = User.objects.get(username='testuser1')
        contact = Contacts.objects.get(owner=login_user.pk)
        response = self.client.get(reverse('delete_contact', kwargs={'pk': contact.pk}))
        self.assertEqual(response.status_code, 302)

    def test_view_logged_in_user_download_contacts(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get(reverse('csv_contacts'))
        self.assertEqual(response.status_code, 200)

    def test_view_logged_in_user_search_contacts(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        data = json.dumps({'searchText': 'test'})
        response = self.client.generic('POST', reverse('search-contact'), data)
        self.assertEqual(response.status_code, 200)


class UserViewsTest(TestCase):

    def setUp(self):
        # Create  user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK', phone='09191919191',
                                              recovery='Phone', active_phone=True)
        test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD',
                                              email_address='alaki@gmail.com',
                                              recovery='Email', active_email=True)
        test_user3 = User.objects.create_user(username='testuser3', password='2HJ1vRV0Z&3iD',
                                              email_address='alaki2@gmail.com',
                                              recovery='Email', active_email=False)
        test_user1.save()
        test_user2.save()
        test_user3.save()

    def test_view_user_recover_password(self):
        data = {'username': 'gholi1@gmz.com'}
        response = self.client.generic('POST', reverse('recovery_link'), data)
        # Check if the view works fine
        self.assertEqual(response.status_code, 302)
        # Check when the user dose not exist it redirects correctly
        self.assertRedirects(response, '/accounts/recover-link/')
        # Check for the correct redirect message if the user recovery option is phone
        data = {'username': 'testuser1'}
        response = self.client.post(reverse('recovery_link'), data, follow=True)
        message = list(response.context.get('messages'))[0]
        self.assertEqual("We sent your phone the recover link please check.", message.message)
        # Check for the correct redirect message if the user recovery option is email
        data = {'username': 'testuser2'}
        response = self.client.post(reverse('recovery_link'), data, follow=True)
        message = list(response.context.get('messages'))[0]
        self.assertEqual("We sent your email recover link please check.", message.message)
        # Check for the correct redirect message if the user recovery option is not active
        data = {'username': 'testuser3'}
        response = self.client.post(reverse('recovery_link'), data, follow=True)
        message = list(response.context.get('messages'))[0]
        self.assertEqual("You didn't verify your email!", message.message)

    def test_view_login_page(self):
        data = {"username": "testuser3", "password": "2HJ1vRV0Z&3iD"}
        response = self.client.post(reverse('login'), data, follow=True)
        message = list(response.context.get('messages'))[0]
        # Check when the user did not activate email of recovery return the correct message and url
        self.assertEqual("Email is not verified, please check your email inbox", message.message)
        self.assertRedirects(response, '/accounts/login/')

    def test_view_register(self):
        data = {
            "username": "testuser5",
            "password": "1XISRUkw+tuK",
            "email_address": "alaki5@gmail.com",
            "phone": '',
            "first_name": "",
            "last_name": "",
            "birth_date": "",
            "recovery": "Email"
        }
        response = self.client.post(reverse('register'), data, follow=True, )

        message = list(response.context.get('messages'))[0]
        self.assertEqual("We sent you an email to verify your account", message.message)
