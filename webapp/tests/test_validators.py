import datetime

from django.forms import ValidationError
from django.test import TestCase

from webapp.validators import validate_range


class ValidateDateRangeTests(TestCase):
    def test_valid_numberic_range(self):
        class NumbericRange:
            start = 1
            stop = 2

        try:
            validate_range(NumbericRange())
        except ValidationError as e:
            self.fail(f"ValidationError raised: {e}")

    def test_invalid_numberic_range(self):
        class NumbericRange:
            start = 2
            stop = 1

        with self.assertRaises(ValidationError):
            validate_range(NumbericRange())

    def test_valid_date_range(self):
        class DateRange:
            start = datetime.date(2023, 1, 1)
            stop = datetime.date(2023, 1, 2)

        try:
            validate_range(DateRange())
        except ValidationError as e:
            self.fail(f"ValidationError raised: {e}")

    def test_invalid_date_range(self):
        class DateRange:
            start = datetime.date(2023, 1, 2)
            stop = datetime.date(2023, 1, 1)

        with self.assertRaises(ValidationError):
            validate_range(DateRange())

    def test_only_start_exists(self):
        class RangeWithOnlyStart:
            start = datetime.date(2023, 1, 2)
            stop = None

        try:
            validate_range(RangeWithOnlyStart())
        except ValidationError as e:
            self.fail(f"ValidationError raised: {e}")

    def test_only_stop_exists(self):
        class RangeWithOnlyStop:
            start = None
            stop = datetime.date(2023, 1, 2)

        try:
            validate_range(RangeWithOnlyStop())
        except ValidationError as e:
            self.fail(f"ValidationError raised: {e}")

    def test_neither_start_nor_stop_exists(self):
        class RangeWithNeither:
            start = None
            stop = None

        try:
            validate_range(RangeWithNeither())
        except ValidationError as e:
            self.fail(f"ValidationError raised: {e}")
