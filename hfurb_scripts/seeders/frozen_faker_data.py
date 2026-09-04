import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

DATA_PATH = Path(__file__).parent / "frozen_faker_output.json"


def _parse_value(method: str, value: Any) -> Any:
    if method == "date_of_birth":
        return date.fromisoformat(value)
    if method == "date_time_between":
        return datetime.fromisoformat(value)
    return value


class FrozenFaker:
    """Drop-in replacement for a Faker instance, backed by a fixed,
    pre-recorded set of values (frozen_faker_output.json).

    Each method returns the next value from that recorded sequence instead
    of generating a new random one, so repeated browser test seed runs
    produce byte-for-byte identical data. Method names and call order must
    match the original recording exactly.
    """

    def __init__(self, log: dict[str, list]):
        self._iterators: dict[str, Iterator[Any]] = {
            method: iter(values) for method, values in log.items()
        }

    def __getattr__(self, name: str):
        try:
            iterator = self._iterators[name]
        except KeyError as e:
            raise AttributeError(
                f"No frozen values captured for fake.{name}(). Add new "
                "entries for it to frozen_faker_output.json."
            ) from e

        def next_value(*args, **kwargs) -> Any:
            try:
                value = next(iterator)
            except StopIteration as e:
                raise RuntimeError(
                    f"Ran out of frozen values for fake.{name}() - the "
                    "seeder now calls it more times than were captured. "
                    "Add more entries for it to frozen_faker_output.json."
                ) from e
            return _parse_value(name, value)

        return next_value


def _load() -> dict[str, dict[str, list]]:
    with DATA_PATH.open() as f:
        return json.load(f)


_frozen_data = _load()
helpers_fake = FrozenFaker(_frozen_data["helpers"])
mutators_fake = FrozenFaker(_frozen_data["mutators"])
