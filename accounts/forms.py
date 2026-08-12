from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Layout
from django.contrib.auth.forms import AuthenticationForm


class GdsAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.pop("autofocus", None)
        self.fields["username"].error_messages["required"] = "Enter your email address"
        self.fields["password"].error_messages["required"] = "Enter your password"

        self.helper = FormHelper()
        self.helper.layout = Layout("username", "password", Button("submit", "Sign in"))
