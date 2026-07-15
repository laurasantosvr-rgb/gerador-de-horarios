from src.models.holiday import Holiday
from src.services.loaders.base_loader import BaseLoader


class HolidayLoader(BaseLoader):
    """Converte a folha Feriados em objetos Holiday."""

    def create_object(self, row):

        return Holiday(
            data=row["Data"].date(),
            nome=row["Nome"],
        )