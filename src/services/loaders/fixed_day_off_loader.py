from src.models.fixed_day_off import FixedDayOff
from src.services.loaders.base_loader import BaseLoader


class FixedDayOffLoader(BaseLoader):
    """Carrega as folgas fixas."""

    def create_object(self, row):

        return FixedDayOff(
            employee_id=int(row["Colaborador ID"]),
            weekday=row["Dia da Semana"].strip().lower(),
        )