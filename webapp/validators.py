from django.forms import ValidationError


def validate_range(value):
    if all([value, value.start, value.stop]) and (value.start > value.stop):
        raise ValidationError("Incorrect range", code="invalid_range")
