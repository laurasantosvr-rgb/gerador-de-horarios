from dataclasses import dataclass


@dataclass(slots=True)
class Reinforcement:
    """Representa um reforço preferencial."""

    unit: str
    employee_id: int
    priority: int