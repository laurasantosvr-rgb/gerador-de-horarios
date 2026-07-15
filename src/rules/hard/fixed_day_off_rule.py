from src.rules.hard.base_rule import BaseRule


class FixedDayOffRule(BaseRule):

    name = "Fixed Day Off Rule"

    description = (
        "Impede atribuições em dias de folga fixa."
    )

    def is_valid(
        self,
        employee,
        unit,
        day,
        hotel,
        schedule,
    ) -> bool:

        weekday = (
            day.strftime("%A").lower()
        )

        translation = {
            "monday": "segunda",
            "tuesday": "terça",
            "wednesday": "quarta",
            "thursday": "quinta",
            "friday": "sexta",
            "saturday": "sábado",
            "sunday": "domingo",
        }

        weekday = translation[weekday]

        for fixed_day in hotel.fixed_days_off:

            if (
                fixed_day.employee_id == employee.id
                and fixed_day.weekday == weekday
            ):
                return False

        return True