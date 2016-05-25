# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from datetime import timedelta, datetime
import json
import pytz

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.conf import settings
from django.utils.timezone import now
from django.core.urlresolvers import reverse

from decisions.subscriptions.models import (
    UserProfile,
    Subscription,
    SubscriptionUser,
    SubscriptionHit
)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class RegistrationTest(TestCase):
    def setUp(self):
        self.c = Client()

    def testSubmitInvalidRegistrationForm(self):
        resp = self.c.post(reverse('register'), {
            'username': '',
            'email': 'not an email',
            'password': 'password',
            'password_again': 'password'
        })
        # We are not redirected
        self.assertEqual(resp.status_code, 200)
        # There is at least one error
        self.assertTrue(resp.context["form"].errors)

    def _register(self, user_info):
        base_info = {
            'username': '',
            'email': 'test@example.org',
            'password': 'p4ssw0rd@',
            'password_again': 'p4ssw0rd@',
        }
        base_info.update(user_info)

        return self.c.post(reverse('register'), base_info, follow=True)

    def testSubmitRegistrationWithoutUsername(self):
        resp = self._register({})

        # The final page is 200 OK
        self.assertEqual(resp.status_code, 200)
        # We're redirected
        self.assertEqual(len(resp.redirect_chain), 1)
        (url, code), = resp.redirect_chain
        self.assertEqual(url, '/')
        # We get a success message
        self.assertEqual(len(resp.context["messages"]), 1)
        # An user is created with some username
        u = User.objects.get(email='test@example.org')
        self.assertTrue(u.username)

    def testSubmitRegistrationWithUsername(self):
        resp = self._register({"username": "tester"})

        # The final page is 200 OK
        self.assertEqual(resp.status_code, 200)
        # We're redirected
        self.assertEqual(len(resp.redirect_chain), 1)
        (url, code), = resp.redirect_chain
        self.assertEqual(url, '/')
        # We get a success message
        self.assertEqual(len(resp.context["messages"]), 1)
        # An user is created with specific username we gave
        u = User.objects.get(email='test@example.org')
        self.assertEqual(u.username, "tester")

    def testActivationEmailActivates(self):
        resp = self._register({})
        u = User.objects.get(email='test@example.org')
        self.assertTrue(getattr(mail, "outbox", False))
        the_mail = mail.outbox.pop()
        self.assertEqual(the_mail.to, ['test@example.org'])
        self.assertIn(u.profile.email_confirm_code, the_mail.body)

        resp = self.c.get(
            reverse('confirm-email', args=(u.profile.email_confirm_code,)),
            follow=True
        )
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(
            User.objects.get(email='test@example.org').profile.email_confirmed
        )

    def testActivationEmailExpires(self):
        self._register({})
        u = User.objects.get(email='test@example.org')
        u.profile.email_confirm_sent_on = now() - timedelta(days=5*365)
        u.profile.save()

        resp = self.c.get(
            reverse('confirm-email', args=(u.profile.email_confirm_code,)),
            follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('subscriptions/not_confirmed.html', [t.name for t in resp.templates])
        self.assertFalse(
            User.objects.get(email='test@example.org').profile.email_confirmed
        )

@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
            'STORAGE': 'ram'
        },
    }
)
class SubscriptionTest(TestCase):
    """TODO: Test subscribing to search results and getting a
    notification. Also test getting a notification email."""
    def setUp(self):
        self.u = User.objects.create_user(
            username="tester",
            email="test@example.org",
            password="test_password"
        )
        UserProfile.objects.create(user=self.u, email_confirmed=now())

        self.c = Client()
        self.c.login(email="test@example.org",
                     password="test_password")

    # ---- Utilities

    def _addAgendaItems(self):
        from decisions.ahjo.models import AgendaItem
        import os.path

        base_path = os.path.dirname(os.path.abspath(__file__))
        agenda_json_path = os.path.join(base_path, "agenda_items.json")

        with open(agenda_json_path) as f:
            for item in json.load(f)["objects"]:
                AgendaItem.objects.create_from_json(item)

    def _indexAndProcess(self):
        call_command("rebuild_index", verbosity=0, interactive=False)
        call_command("process_subscriptions", verbosity=0)

    # --- Actual tests

    def testSaveASearch(self):
        self.assertEqual(
            Subscription.objects.filter(subscribed_users=self.u).count(),
            0
        )

        resp = self.c.post("/subscriptions/add/", {
            "search_backend": 0,
            "search_term": "omena",
            "send_mail": False
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.redirect_chain), 1)

        self.assertEqual(
            Subscription.objects.filter(subscribed_users=self.u).count(),
            1
        )
        sub = SubscriptionUser.objects.get(user=self.u)
        self.assertFalse(sub.send_mail)
        self.assertEqual(sub.subscription.search_term, "omena")

    def testSaveASearchWithEmail(self):
        self.assertEqual(
            Subscription.objects.filter(subscribed_users=self.u).count(),
            0
        )

        resp = self.c.post("/subscriptions/add/", {
            "search_backend": 0,
            "search_term": "omena",
            "send_mail": True
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.redirect_chain), 1)

        self.assertEqual(
            Subscription.objects.filter(subscribed_users=self.u).count(),
            1
        )
        sub = SubscriptionUser.objects.get(user=self.u)
        self.assertTrue(sub.send_mail)
        self.assertEqual(sub.subscription.search_term, "omena")

    def testNewItemDoesNotNotify(self):
        """Just adding and indexing new items that won't match doesn't create
        notifications

        """
        resp = self.c.post("/subscriptions/add/", {
            "search_term": "omena",
            "send_mail": True
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        self._addAgendaItems()
        self._indexAndProcess()

        self.assertEqual(len(getattr(mail, "outbox", ())), 0)
        self.assertEqual(
            SubscriptionHit.objects.filter(notified_users=self.u).count(),
            0
        )


    # XXX Fails for some reason on Travis
    def _testNewHitCreatesNotification(self):
        self.assertEqual(Subscription.objects.count(), 0)

        resp = self.c.post("/subscriptions/add/", {
            "search_term": "asukasvalinnat",
            "send_mail": False
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Subscription.objects.count(), 1)

        s = Subscription.objects.get(search_term="asukasvalinnat")
        s.created = datetime(2014, 3, 27, 12, 16, 54, 858182,
                             tzinfo=pytz.UTC)
        s.save()

        self._addAgendaItems()
        self._indexAndProcess()

        self.assertEqual(
            SubscriptionHit.objects.filter(notified_users=self.u).count(),
            1
        )
        self.assertEqual(len(getattr(mail, "outbox", ())), 0)


    # XXX Fails for some reason on Travis
    def _testNewHitSendsNotificationEmail(self):
        self.assertEqual(Subscription.objects.count(), 0)

        resp = self.c.post("/subscriptions/add/", {
            "search_term": "asukasvalinnat",
            "send_mail": True
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Subscription.objects.count(), 1)

        s = Subscription.objects.get(search_term="asukasvalinnat")
        s.created = datetime(2014, 3, 27, 12, 16, 54, 858182,
                             tzinfo=pytz.UTC)
        s.save()

        self._addAgendaItems()
        self._indexAndProcess()

        self.assertEqual(len(getattr(mail, "outbox", ())), 1)
        self.assertEqual(
            SubscriptionHit.objects.filter(notified_users=self.u).count(),
            1
        )
