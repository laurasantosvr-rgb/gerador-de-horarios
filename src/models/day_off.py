from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class DayOff:
    """Representa um dia de folga."""

    employee_id: int
    day: date