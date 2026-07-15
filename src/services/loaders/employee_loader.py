from src.models.employee import Employee
from src.services.loaders.base_loader import BaseLoader
from src.utils.converters import to_bool


class EmployeeLoader(BaseLoader):

    def create_object(self, row):

        return Employee(
            id=int(row["ID"]),
            nome=row["Nome"],
            ativo=to_bool(row["Ativo"]),
            horas_por_dia=int(row["Horas por dia"]),
            unidade_principal=row["Unidade principal"],
            pode_rodar=to_bool(row["Pode rodar"]),
            trabalha_fins_de_semana=to_bool(row["Trabalha fins de semana"]),
            trabalha_feriados=to_bool(row["Trabalha feriados"]),
        )

    def load(self):
        employees = super().load()

        return {
            employee.id: employee
            for employee in employees
        }