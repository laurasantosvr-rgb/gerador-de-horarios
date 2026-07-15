from src.models.reinforcement import Reinforcement
from src.services.loaders.base_loader import BaseLoader


class ReinforcementLoader(BaseLoader):
    """Converte a folha Reforcos em objetos Reinforcement."""

    def create_object(self, row):

        return Reinforcement(
            unit=row["Unidade"],
            employee_id=int(row["Colaborador ID"]),
            priority=int(row["Prioridade"]),
        )