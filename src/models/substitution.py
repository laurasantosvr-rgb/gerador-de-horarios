from dataclasses import dataclass


@dataclass(slots=True)
class Substitution:
    """Representa uma substituição preferencial."""

    employee_id: int
    substitute_id: int
    priority: int