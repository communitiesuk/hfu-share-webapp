from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Field, Fluid, Layout
from django.contrib.auth.forms import AuthenticationForm


class GdsAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("username", field_width=Fluid.ONE_HALF),
            Field.text("password", field_width=Fluid.ONE_HALF),
            Button("submit", "Sign in"),
        )
