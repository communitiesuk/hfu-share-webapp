from django_filters.fields import DateRangeField, RangeField

from webapp.validators import validate_range


class CustomDateRangeField(DateRangeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.validators.append(validate_range)


class CustomRangeField(RangeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.validators.append(validate_range)
