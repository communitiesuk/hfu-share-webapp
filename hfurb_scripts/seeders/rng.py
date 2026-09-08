import random

from faker import Faker

rng = random.Random()
fake = Faker("en_GB")


def seed_seeders(seed: int) -> None:
    rng.seed(seed)
    fake.seed_instance(seed)
