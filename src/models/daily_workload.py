from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class DailyWorkload:
    """Representa a carga diária de uma unidade."""

    data: date
    unidade: str
    checkouts: int
    stayovers: int