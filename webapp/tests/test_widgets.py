from django.test import SimpleTestCase

from webapp.widgets import MultiValueWidget


class MultiValueWidgetTest(SimpleTestCase):
    def test_render_with_multiple_values(self):
        widget = MultiValueWidget("Email")
        html = widget.render(
            name="emails", value=["a@example.com", "b@example.com"], attrs={}
        )
        self.assertIn('for="id_emails"', html)
        self.assertIn('name="emails-0"', html)
        self.assertIn('id="id_emails"', html)
        self.assertIn('value="a@example.com"', html)
        self.assertIn('for="id_emails-1"', html)
        self.assertIn('name="emails-1"', html)
        self.assertIn('id="id_emails-1"', html)
        self.assertIn('value="b@example.com"', html)
        self.assertIn('class="array-input-group"', html)

    def test_render_empty(self):
        widget = MultiValueWidget("Email")
        html = widget.render(name="emails", value=None, attrs={})
        self.assertIn('for="id_emails"', html)
        self.assertIn('name="emails-0"', html)
        self.assertIn('id="id_emails"', html)
        self.assertIn('value=""', html)

    def test_value_from_datadict(self):
        widget = MultiValueWidget("Email")
        data = {
            "emails-0": "test1@example.com",
            "emails-1": "test2@example.com",
            "emails-2": "",
        }
        value = widget.value_from_datadict(data, files=None, name="emails")
        self.assertEqual(value, ["test1@example.com", "test2@example.com"])
