from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Assignment:
    """Representa uma atribuição de trabalho."""

    employee_id: int
    day: date
    unit: str
    minutes: int