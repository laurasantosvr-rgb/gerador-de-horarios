from src.models.substitution import Substitution
from src.services.loaders.base_loader import BaseLoader


class SubstitutionLoader(BaseLoader):
    """Converte a folha Substituicoes em objetos Substitution."""

    def create_object(self, row):

        return Substitution(
            employee_id=int(row["Colaborador ID"]),
            substitute_id=int(row["Substituto ID"]),
            priority=int(row["Prioridade"]),
        )