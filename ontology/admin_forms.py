from django import forms


class DateRangeForm(forms.Form):
    start = forms.DateField(required=False, label="")
    end = forms.DateField(required=False, label="")
