from enum import Enum
from typing import Final


LAST_UPDATED_KEY: Final[str] = "___last_updated___"


class DomainStatus(Enum):
    REGISTERED = 0
    UNREGISTERED = 1
    AVAILABLE_FOR_APPLICATION = 2
    PREMIUM = 3
    FAILED = 4


__all__: Final[tuple[str, ...]] = (
    "LAST_UPDATED_KEY",
)
