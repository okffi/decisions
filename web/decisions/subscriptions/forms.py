from django import forms
from django.utils.translation import ugettext_lazy as _, string_concat
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import (
    validate_password, password_validators_help_text_html
)
from django.contrib.auth.models import User

from decisions.subscriptions.models import Subscription


class RegisterForm(forms.Form):
    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("user@example.com"),
                "class": "form-control"
            }
        ),
    )
    username = forms.CharField(
        label=_("Display name"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label=_("Password")
    )
    password_again = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
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
                "class": "form-control"
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label=_("Password")
    )
    next = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean(self):
        self.user = authenticate(**self.cleaned_data)
        if not self.user:
            raise forms.ValidationError(_("Email or password did not match. Please try again."))
        return self.cleaned_data

class SubscriptionForm(forms.Form):
    search_term = forms.CharField(
        label=_('Search term'),
        widget=forms.TextInput(
            attrs={
            "class": "form-control"
            })
    )
    send_mail = forms.BooleanField(
        label=_('Sends email'),
        help_text=_('If checked, notifications about new search results are also sent by email. Otherwise they will just show up in your feed.'),
        required=False
    )

class SubscriptionEditForm(SubscriptionForm):
    active = forms.BooleanField(
        label=_('Active'),
        help_text=_('If you do not wish to receive any more notifications from this subscriptions, you can disable it. Old notifications will not disappear from your feed.'),
        required=False
    )
