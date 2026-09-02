from factory import LazyFunction
from faker import Faker

fake = Faker()


def unique_faker(provider: str, **kwargs):
    return LazyFunction(lambda: getattr(fake.unique, provider)(**kwargs))
