from src.rules.hard.base_rule import BaseRule


class WeekendEligibilityRule(BaseRule):
    """Verifica se o colaborador pode trabalhar ao fim de semana."""

    name = "Weekend Eligibility Rule"

    description = (
        "Verifica se o colaborador pode trabalhar "
        "ao sábado e domingo."
    )

    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        if day.weekday() not in (5, 6):
            return True

        return employee.trabalha_fins_de_semana