from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Holiday:
    """Representa um feriado."""

    data: date
    nome: str