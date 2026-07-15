import json
from pathlib import Path


class HistoryManager:
    """
    Guarda estatísticas históricas
    dos colaboradores.
    """

    def __init__(
        self,
        path="history.json",
    ):

        self.path = Path(path)

        self.data = {
            "processed_files": [],
            "employees": {},
        }

        self.load()

    def load(self):
        """
    Carrega o histórico.
    """

        if not self.path.exists():
            return

        with open(
            self.path,
            "r",
            encoding="utf-8",
        ) as file:

            self.data = json.load(file)

        self.data.setdefault(
            "processed_files",
            [],
        )

        self.data.setdefault(
            "employees",
            {},
        )

    def save(self):
        """
        Guarda o histórico.
        """

        with open(
            self.path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4,
                ensure_ascii=False,
            )

    def holiday_offs(
        self,
        employee_id,
    ):
        """
    Devolve o número de feriados
    de folga do colaborador.
    """

        employee = self.data[
            "employees"
        ].get(
            str(employee_id),
            {},
        )

        return employee.get(
            "holiday_offs",
            0,
        )
    
    def update(
        self,
        schedule,
        hotel,
        file_path,
    ):
        """
    Atualiza o histórico com
    o horário importado.
    """
        if file_path is None:
            return

        file_name = Path(
            file_path,
        ).name

        #
        # Se este ficheiro já foi
        # contabilizado, não faz nada.
        #

        if file_name in self.data[
            "processed_files"
        ]:
            return

        for employee in hotel.employees.values():

            employee_data = (
                self.data["employees"]
                .setdefault(
                    str(employee.id),
                    {},
                )
            )
        
            employee_data.setdefault(
                "holiday_offs",
                0,
            )

            employee_data[
                "holiday_offs"
            ] += schedule.count_holidays_off(
                employee.id,
                hotel,
            )

        self.data[
            "processed_files"
        ].append(
           file_name,
        )   

        self.save()