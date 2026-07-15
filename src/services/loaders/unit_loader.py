from src.models.unit import Unit
from src.services.loaders.base_loader import BaseLoader


class UnitLoader(BaseLoader):
    """Converte a folha Unidades em objetos Unit."""

    def create_object(self, row):

        return Unit(
            nome=row["Unidade"],
            checkout_minutos=int(row["Check-out"]),
            stayover_minutos=int(row["Stay-over"]),
            zonas_comuns_minutos=int(row["Zonas comuns"]),
            frequencia_zc=row["Frequência ZC"],
            minimo_colaboradores=int(row["Mínimo de colaboradores"]),
        )

    def load(self):
        units = super().load()

        return {
            unit.nome: unit
            for unit in units
        }