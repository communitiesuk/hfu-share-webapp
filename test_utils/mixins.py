from .faker import fake


class FakerMixin:
    def setUp(self):
        super().setUp()
        self._clear_faker_unique_cache()

    @staticmethod
    def _clear_faker_unique_cache():
        fake.unique.clear()
