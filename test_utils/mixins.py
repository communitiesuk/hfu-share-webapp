from bs4 import BeautifulSoup

from .faker import fake


class FakerMixin:
    def setUp(self):
        super().setUp()
        self._clear_faker_unique_cache()

    @staticmethod
    def _clear_faker_unique_cache():
        fake.unique.clear()


class HTMLAssertionsMixin:
    def assertHTMLEqual(self, actual, expected):
        actual_soup = BeautifulSoup(actual, "html.parser")
        expected_soup = BeautifulSoup(expected, "html.parser")

        self.assertEqual(actual_soup.prettify(), expected_soup.prettify())
