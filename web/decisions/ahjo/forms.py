from django import forms

from decisions.ahjo.models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['selector', 'text']
        widgets = {
            'selector': forms.HiddenInput(),
            'text': forms.Textarea(attrs={"class": "form-control"})
        }
