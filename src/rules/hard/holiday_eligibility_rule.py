from src.rules.hard.base_rule import BaseRule


class HolidayEligibilityRule(BaseRule):
    """Verifica se o colaborador pode trabalhar num feriado."""

    name = "Holiday Eligibility Rule"

    description = (
        "Verifica se o colaborador está autorizado "
        "a trabalhar em feriados."
    )

    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        is_holiday = any(
            holiday.data == day
            for holiday in hotel.holidays
        )

        if not is_holiday:
            return True

        return employee.trabalha_feriados