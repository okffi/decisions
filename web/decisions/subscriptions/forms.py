from __future__ import unicode_literals

from django import forms
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _, string_concat
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import (
    validate_password, password_validators_help_text_html
)
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from decisions.subscriptions.models import Subscription
from decisions.geo.views import geocode


class RegisterForm(forms.Form):
    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("user@example.com"),
                "autocomplete": "username",
            }
        ),
    )
    username = forms.CharField(
        label=_("Display name"),
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "nickname"
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password"
        }),
        label=_("Password")
    )
    password_again = forms.CharField(
        widget=forms.PasswordInput(),
        label=_("Password again"),
        help_text=string_concat(
            _("Your password must meet these requirements:"),
            password_validators_help_text_html())
    )

    def clean(self):
        if ("password" in self.cleaned_data
            and "password_again" in self.cleaned_data):
            if self.cleaned_data["password"] != self.cleaned_data["password_again"]:
                self.add_error("password",
                               forms.ValidationError(_("Passwords don't match")))
                self.add_error("password_again",
                               forms.ValidationError(_("Passwords don't match")))

        if "email" in self.cleaned_data:
            self.cleaned_data["username"] = self.get_username()

        if "username" in self.cleaned_data:
            username_exists = User.objects.filter(
                username=self.cleaned_data["username"]).count()
            if username_exists:
                self.add_error("username", forms.ValidationError(
                    _("Please choose another display name")))

        if "email" in self.cleaned_data:
            email_exists = User.objects.filter(
                email=self.cleaned_data["email"]).count()
            if email_exists:
                self.add_error("email", forms.ValidationError(
                    _("Please choose another email address")))

        if "password" in self.cleaned_data:
            validate_password(self.cleaned_data["password"])

        return self.cleaned_data

    def get_username(self):
        if self.cleaned_data.get("username"):
            return self.cleaned_data["username"]
        return self.cleaned_data["email"].split("@", 1)[0]

class LoginForm(forms.Form):
    user = None

    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("user@example.com"),
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password"
        }),
        label=_("Password")
    )
    next = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean(self):
        self.user = authenticate(**self.cleaned_data)
        if not self.user:
            raise forms.ValidationError(_("Email or password did not match. Please try again."))
        return self.cleaned_data

class BSRadioChoiceInput(widgets.RadioChoiceInput):
    def render(self, name=None, value=None, attrs=None, choices=()):
        from django.utils.html import format_html

        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        active = "active" if self.is_checked() else ""
        return format_html(
            '<label{} class="btn {}">{} {}</label>', label_for, active, self.tag(attrs), self.choice_label
        )

class BSRadioFieldRenderer(widgets.ChoiceFieldRenderer):
    choice_input_class = BSRadioChoiceInput
    outer_html = '<div{id_attr} class="btn-group" data-toggle="buttons">{content}</div>'
    inner_html = '{choice_value}{sub_widgets}'

class BSRadioSelect(forms.RadioSelect):
    renderer = BSRadioFieldRenderer

class SubscriptionForm(forms.Form):
    search_backend = forms.ChoiceField(
        label=_("Search type"),
        choices=Subscription.BACKEND_CHOICES,
        widget=BSRadioSelect
    )
    search_term = forms.CharField(
        label=_('Search term or location'),
        widget=forms.TextInput(
            attrs={
            })
    )

    DISTANCE_CHOICES = (
        (100, _("100 m")),
        (500, _("500 m")),
        (1000, _("1km")),
        (3000, _("3km")),
    )
    distance_meters = forms.ChoiceField(
        label=_("Perimeter distance"),
        choices=DISTANCE_CHOICES,
        initial=1000,
        widget=BSRadioSelect,
        required=False
    )

    send_mail = forms.BooleanField(
        label=_('Sends email'),
        help_text=_('If checked, notifications about new search results are also sent by email. Otherwise they will just show up in your feed.'),
        required=False,
        widget=BSRadioSelect(choices=[
            (True, _("Sends email")),
            (False, _("No"))
        ])
    )

    def clean_search_backend(self):
        return int(self.cleaned_data["search_backend"])

    def clean(self):
        if "search_backend" in self.cleaned_data:
            backend = self.cleaned_data["search_backend"]
            if backend == Subscription.GEO:
                # validate that search term geocodes to a point and
                # that we have a valid distance
                if "distance_meters" not in self.cleaned_data:
                    self.add_error("distance_meters",
                                   forms.ValidationError(_("Map searches must select a perimeter.")))
                self.cleaned_data["distance_meters"] = int(self.cleaned_data["distance_meters"])

                pointdict = geocode(self.cleaned_data["search_term"])
                if not pointdict:
                    self.add_error("search_term",
                                   forms.ValidationError(_("We couldn't find this location. Please describe another location.")))

                self.point = Point(pointdict["coordinates"][1],
                                   pointdict["coordinates"][0])
        return self.cleaned_data


class SubscriptionEditForm(SubscriptionForm):
    active = forms.BooleanField(
        label=_('Active'),
        help_text=_('If you do not wish to receive any more notifications from this subscriptions, you can disable it. Old notifications will not disappear from your feed.'),
        required=False,
        widget=BSRadioSelect(choices=[
            (True, _("Active")),
            (False, _("No"))
        ])
    )

class ChangePasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label=_("Old password"),
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label=_("New password"),
    )
    new_password_again = forms.CharField(
        widget=forms.PasswordInput,
        label=_("New password again"),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        if "password" in self.cleaned_data:
            authenticated_user = authenticate(email=self.user.email,
                                              password=self.cleaned_data["password"])
            if not authenticated_user:
                self.add_error("password",
                               forms.ValidationError(_("Please provide the current password")))

        if ("new_password" in self.cleaned_data
            and "new_password_again" in self.cleaned_data):
            if self.cleaned_data["new_password"] != self.cleaned_data["new_password_again"]:
                self.add_error("new_password",
                               forms.ValidationError(_("Passwords don't match")))
                self.add_error("new_password_again",
                               forms.ValidationError(_("Passwords don't match")))

        return self.cleaned_data

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label=_("Email address"),
        help_text=_("Please provide your email address. We will send password reset instructions there.")
    )

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label=_("New password"),
    )
    new_password_again = forms.CharField(
        widget=forms.PasswordInput,
        label=_("New password again"),
    )

    def clean(self):
        if ("new_password" in self.cleaned_data
            and "new_password_again" in self.cleaned_data):
            if self.cleaned_data["new_password"] != self.cleaned_data["new_password_again"]:
                self.add_error("new_password",
                               forms.ValidationError(_("Passwords don't match")))
                self.add_error("new_password_again",
                               forms.ValidationError(_("Passwords don't match")))

        return self.cleaned_data
