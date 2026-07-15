from src.rules.hard.base_rule import BaseRule


class VacationRule(BaseRule):
    """Impede colaboradores de trabalharem durante as férias."""

    name = "Vacation Rule"

    description = (
        "Um colaborador não pode ser escalado "
        "durante um período de férias."
    )

    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        for vacation in hotel.vacations:

            if vacation.colaborador_id != employee.id:
                continue

            if vacation.data_inicio <= day <= vacation.data_fim:
                return False

        return True