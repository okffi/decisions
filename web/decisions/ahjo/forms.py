from django import forms
from django.utils.translation import ugettext_lazy as _

from decisions.ahjo.models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['selector', 'text']
        widgets = {
            'selector': forms.HiddenInput(),
            'text': forms.Textarea(attrs={
                "placeholder": _("Write your comment here"),
                "rows": 3,
            })
        }

    def clean_text(self):
        text = self.cleaned_data["text"]

        if len(text) > 300:
            raise forms.ValidationError(_("Comment should be under 300 characters"))

        return text
