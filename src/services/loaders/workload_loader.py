from src.models.daily_workload import DailyWorkload
from src.services.loaders.base_loader import BaseLoader


class WorkloadLoader(BaseLoader):
    """Converte a folha CargaDiaria em objetos DailyWorkload."""

    def create_object(self, row):

        return DailyWorkload(
            data=row["Data"].date(),
            unidade=row["Unidade"],
            checkouts=int(row["Check-outs"]),
            stayovers=int(row["Stay-overs"]),
        )