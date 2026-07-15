from src.rules.hard.base_rule import BaseRule


class DayOffRule(BaseRule):
    """Impede atribuições em dias de folga planeados."""

    name = "Day Off Rule"

    description = (
        "Impede atribuições em dias de folga."
    )

    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        if schedule.is_day_off(
            employee.id,
            day,
        ):
            return False

        return True