from django import forms


class PhoneLookupForm(forms.Form):
    number = forms.CharField(
        label="Номер телефона",
        max_length=32,
        help_text='Можно вводить в формате "+7...", "8...", "7...", без пробелов.',
    )
