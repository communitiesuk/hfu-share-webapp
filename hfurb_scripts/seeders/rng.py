import random

from faker import Faker

# The seeders never use Python's global random module or Faker's shared
# generator. Anything else in the process can draw from those (on dev the Sentry
# log batcher does, from a background thread) and every value generated after
# that draw would change. These private instances are only reachable from here.
rng = random.Random()
fake = Faker("en_GB")


def seed_seeders(seed: int) -> None:
    rng.seed(seed)
    fake.seed_instance(seed)
