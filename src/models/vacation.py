from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Vacation:
    """Representa um período de férias."""

    colaborador_id: int
    data_inicio: date
    data_fim: date
    observacoes: str