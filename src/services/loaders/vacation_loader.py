from src.models.vacation import Vacation
from src.services.loaders.base_loader import BaseLoader


class VacationLoader(BaseLoader):
    """Converte a folha Ferias em objetos Vacation."""

    def create_object(self, row):

        return Vacation(
    colaborador_id=int(row["Colaborador ID"]),
    data_inicio=row["Data de início"].date(),
    data_fim=row["Data de fim"].date(),
    observacoes=row["Observações"],
)