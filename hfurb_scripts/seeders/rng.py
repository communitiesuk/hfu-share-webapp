import random

import factory.random
from faker import Faker

rng = random.Random()
fake = Faker("en_GB")


def seed_seeders(seed: int) -> None:
    from test_utils.faker import fake as factory_fake

    rng.seed(seed)
    fake.seed_instance(seed)
    factory_fake.seed_instance(seed)
    factory_fake.unique.clear()
    factory.random.reseed_random(seed)
