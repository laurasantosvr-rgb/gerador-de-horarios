from dataclasses import dataclass


@dataclass(slots=True)
class FixedDayOff:
    """Representa um dia fixo de folga."""

    employee_id: int
    weekday: str