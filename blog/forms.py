from django import forms

class EmailPostForm(forms.Form):
    name = forms.CharField(
        max_length=30,
    )
    to = forms.EmailField()
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )
