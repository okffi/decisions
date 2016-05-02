from django import forms
from django.utils.translation import ugettext_lazy as _

from decisions.comments.models import Comment

COMMENT_WIDGET = forms.Textarea(attrs={
    "placeholder": _("Write your comment here"),
    "rows": 3,
})

class ValidationMixin(object):
    def clean_text(self):
        text = self.cleaned_data["text"]

        if len(text) > 300:
            raise forms.ValidationError(_("Comment should be under 300 characters"))

        return text

class CommentForm(forms.ModelForm, ValidationMixin):
    class Meta:
        model = Comment
        fields = ['selector', 'text']
        widgets = {
            'selector': forms.HiddenInput(),
            'text': COMMENT_WIDGET,
        }

class EditCommentForm(forms.ModelForm, ValidationMixin):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': COMMENT_WIDGET}
