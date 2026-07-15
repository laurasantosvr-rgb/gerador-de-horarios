from src.rules.soft.base_rule import BaseRule


class HolidayBalanceRule(BaseRule):
    """Avalia o equilíbrio da distribuição dos feriados."""

    name = "Holiday Balance Rule"

    description = (
        "Os feriados devem ser distribuídos "
        "de forma equilibrada."
    )

    weight = 50

    def penalty(
        self,
        schedule,
        hotel,
        year,
        month,
    ) -> int:

        holidays_per_employee = []

        for employee in hotel.employees.values():

            # Apenas colaboradores elegíveis
            if not employee.trabalha_feriados:
                continue

            worked = schedule.count_holidays_worked(
                employee.id,
                hotel,
            )

            holidays_per_employee.append(worked)

        if len(holidays_per_employee) < 2:
            return 0

        difference = (
            max(holidays_per_employee)
            - min(holidays_per_employee)
        )

        return difference * self.weight