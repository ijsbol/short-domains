from enum import Enum
import itertools
import string
from typing import Final


LAST_UPDATED_KEY: Final[str] = "___last_updated___"


class DomainStatus(Enum):
    REGISTERED = 0
    UNREGISTERED = 1
    AVAILABLE_FOR_APPLICATION = 2
    PREMIUM = 3
    FAILED = 4


def generate_strings_to_check(size: int) -> list[str]:
    """Generate all possible x-length domain combinations."""
    letters = string.ascii_lowercase + string.digits
    return [''.join(s) for s in itertools.product(letters, repeat=size)]


__all__: Final[tuple[str, ...]] = (
    "LAST_UPDATED_KEY",
    "generate_strings_to_check",
)
